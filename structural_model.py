#!/usr/bin/env python3
"""
Structural General Equilibrium Model: Dekle-Eaton-Kortum exact-hat algebra
===========================================================================
Calibrated to 2024 low-carbon technology trade matrix.
Simulates 6 counterfactual policy scenarios for the Green Trade Trilemma.
"""
import pandas as pd, numpy as np, os, io, zipfile, csv as csv_mod
import json

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "raw")
PROC = os.path.join(BASE, "data", "processed")
os.makedirs(PROC, exist_ok=True)

# ===================================================================
# 1. BUILD 2024 BILATERAL TRADE MATRIX
# ===================================================================
print("Building 2024 trade matrix...")

baci = pd.read_csv(os.path.join(RAW, "baci_low_carbon_trade.csv"))
baci = baci[baci["year"] == 2024].copy()

# Country code mapping
with zipfile.ZipFile(os.path.join(RAW, "BACI_HS12_V202601.zip"), 'r') as zf:
    cc_file = [n for n in zf.namelist() if 'country_codes' in n.lower()][0]
    with zf.open(cc_file) as f:
        text = io.TextIOWrapper(f, encoding='utf-8', errors='replace')
        reader = csv_mod.reader(text)
        next(reader)
        code_map, rev_map = {}, {}
        for row in reader:
            if len(row) >= 4 and row[3]:
                code_map[int(row[0])] = row[3]
                rev_map[row[3]] = row[1]
        text.detach()

baci["exporter_iso3"] = baci["exporter_iso"].map(code_map)
baci["importer_iso3"] = baci["importer_iso"].map(code_map)
baci = baci.dropna(subset=["exporter_iso3", "importer_iso3"])

# Aggregate bilateral flows
flows = baci.groupby(["exporter_iso3", "importer_iso3"])["value_kusd"].sum().reset_index()

# Select top 40 countries by total trade
total_by_cty = pd.concat([
    flows.groupby("exporter_iso3")["value_kusd"].sum(),
    flows.groupby("importer_iso3")["value_kusd"].sum(),
]).groupby(level=0).sum().sort_values(ascending=False)

TOP_N = 40
top_countries = total_by_cty.head(TOP_N).index.tolist()
print(f"  Selected top {len(top_countries)} countries (of {len(total_by_cty)} total)")

# Build trade matrix (exporter × importer)
all_ctys = sorted(top_countries)
N = len(all_ctys)
cty_idx = {c: i for i, c in enumerate(all_ctys)}

X = np.zeros((N, N))
for _, row in flows.iterrows():
    exp = row["exporter_iso3"]
    imp = row["importer_iso3"]
    if exp in cty_idx and imp in cty_idx:
        X[cty_idx[exp], cty_idx[imp]] += row["value_kusd"]

# Add small diagonal to avoid zeros
np.fill_diagonal(X, np.maximum(np.diag(X), X.sum(axis=1) * 0.001))

# Compute trade shares π_{ij} = X_{ij} / Σ_k X_{kj}
total_imports = X.sum(axis=0, keepdims=True)
pi = X / np.maximum(total_imports, 1.0)

print(f"  Trade matrix: {N}×{N}, total flow = ${X.sum()/1e6:.0f}B")

# ===================================================================
# 2. PARAMETERS
# ===================================================================
THETA = 4.2          # Trade elasticity (gravity literature)
LEARNING_RATE = 0.19 # Solar learning rate (Way et al. 2022)
CHN_IDX = cty_idx.get("CHN", -1)

# High-income countries (for decoupling scenarios)
HIGH_INCOME = {"USA", "CAN", "GBR", "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "SWE",
               "NOR", "DNK", "FIN", "AUT", "CHE", "IRL", "PRT", "GRC", "LUX", "ISL",
               "AUS", "NZL", "JPN", "KOR", "SGP", "HKG", "TWN"}
G7 = {"USA", "CAN", "GBR", "DEU", "FRA", "ITA", "JPN"}
G20 = G7 | {"AUS", "KOR", "ZAF", "TUR", "SAU", "IND", "IDN", "MEX", "BRA", "ARG", "RUS", "CHN"}
DEVELOPING = set(all_ctys) - HIGH_INCOME

# ===================================================================
# 3. EXACT-HAT SOLVER
# ===================================================================
def solve_dek(pi, tau_hat, theta=THETA, max_iter=2000, tol=1e-8):
    """
    Dekle-Eaton-Kortum exact-hat algebra.
    pi: baseline trade share matrix (N×N, π_{ij} = X_{ij}/Σ_k X_{kj})
    tau_hat: counterfactual trade cost changes (N×N, symmetric)
    Returns: w_hat (wage changes), P_hat (price index changes),
             pi_hat (trade share changes), welfare (real wage changes)
    """
    N_ = pi.shape[0]
    w_hat = np.ones(N_)  # Initial guess: wages unchanged

    for it in range(max_iter):
        # Price index: P̂_j^{-θ} = Σ_i π_{ij} (ŵ_i τ̂_{ij})^{-θ}
        w_tau = w_hat[:, np.newaxis] * tau_hat
        P_hat_neg_theta = (pi * np.power(np.maximum(w_tau, 1e-10), -theta)).sum(axis=0)
        P_hat = np.power(np.maximum(P_hat_neg_theta, 1e-10), -1.0 / theta)

        # Trade balance: ŵ_j = (Σ_i π_{ji} P̂_i^{θ} / Σ_k π_{ki} P̂_k^{θ})^{1/θ}
        # Simplified: assume balanced trade → income = expenditure
        P_hat_theta = np.power(P_hat, theta)
        numer = (pi * P_hat_theta[np.newaxis, :]).sum(axis=1)
        denom = (pi * P_hat_theta[np.newaxis, :]).sum(axis=0)
        w_new = np.power(np.maximum(numer / np.maximum(denom, 1e-10), 1e-10), 1.0 / theta)

        if np.max(np.abs(w_new - w_hat)) < tol:
            w_hat = w_new
            break
        w_hat = 0.7 * w_hat + 0.3 * w_new  # Damping

    # Final price index
    w_tau = w_hat[:, np.newaxis] * tau_hat
    P_hat_neg_theta = (pi * np.power(np.maximum(w_tau, 1e-10), -theta)).sum(axis=0)
    P_hat = np.power(np.maximum(P_hat_neg_theta, 1e-10), -1.0 / theta)

    # Trade share changes
    pi_hat = np.zeros((N_, N_))
    for j in range(N_):
        pi_hat[:, j] = np.power(w_hat * tau_hat[:, j] / max(P_hat[j], 1e-10), -theta)

    # Welfare = ŵ_j / P̂_j (real wage)
    welfare = w_hat / P_hat

    return {"w_hat": w_hat, "P_hat": P_hat, "pi_hat": pi_hat, "welfare": welfare}

# ===================================================================
# 4. COUNTERFACTUAL SCENARIOS
# ===================================================================
print("\nSimulating counterfactual scenarios...")

scenarios = {}
baseline = {"pi": pi.copy(), "name": "Baseline (2024)"}

# Scenario 1: BAU (baseline, no changes)
tau_hat_bau = np.ones((N, N))
scenarios["S1_BAU"] = {"name": "Business as Usual", "tau_hat": tau_hat_bau}

# Scenario 2: Full Decoupling (HI countries block China imports)
tau_hat_decouple = np.ones((N, N))
for i in range(N):
    if all_ctys[i] in HIGH_INCOME and CHN_IDX >= 0:
        tau_hat_decouple[CHN_IDX, i] = 3.0  # Triple trade costs with China
scenarios["S2_Decoupling"] = {"name": "Full Decoupling from China", "tau_hat": tau_hat_decouple}

# Scenario 3: CBAM Extension ($100/tCO2 carbon tariff)
# Approximate: 5-10% cost increase on carbon-intensive imports
tau_hat_cbam = np.ones((N, N))
carbon_intensive = {"CHN", "IND", "RUS", "VNM", "IDN", "ZAF", "TUR"}
for i in range(N):
    if all_ctys[i] in carbon_intensive:
        for j in range(N):
            if i != j:
                tau_hat_cbam[i, j] = 1.08  # 8% carbon tariff
scenarios["S3_CBAM"] = {"name": "CBAM Extension", "tau_hat": tau_hat_cbam}

# Scenario 4: Climate Club (G7 + China zero tariffs)
tau_hat_club = np.ones((N, N))
club = (G7 | {"CHN"}) & set(all_ctys)
club_indices = [cty_idx[c] for c in club if c in cty_idx]
for i in club_indices:
    for j in club_indices:
        if i != j:
            tau_hat_club[i, j] = 0.85  # 15% reduction in trade costs
scenarios["S4_ClimateClub"] = {"name": "Climate Club (G7+China)", "tau_hat": tau_hat_club}

# Scenario 5: Inclusive Green Trade (Scenario 4 + tech transfer + concessional finance)
tau_hat_inclusive = tau_hat_club.copy()
# Technology transfer: reduce entry costs for developing countries by 15%
dev_indices = [cty_idx[c] for c in (DEVELOPING & set(all_ctys)) if c in cty_idx and c != "CHN"]
for i in dev_indices:
    tau_hat_inclusive[i, :] *= 0.85  # 15% cheaper to import from developing countries
# Concessional finance: reduce trade costs to developing countries
for j in dev_indices:
    tau_hat_inclusive[:, j] *= 0.93  # 7% cheaper for developing countries to import
scenarios["S5_Inclusive"] = {"name": "Inclusive Green Trade", "tau_hat": tau_hat_inclusive}

# Scenario 6: China Export Restriction
tau_hat_export = np.ones((N, N))
if CHN_IDX >= 0:
    tau_hat_export[CHN_IDX, :] = 2.0  # Double cost of Chinese exports globally
scenarios["S6_ExportRestrict"] = {"name": "China Export Restrictions", "tau_hat": tau_hat_export}

# ===================================================================
# 5. SOLVE ALL SCENARIOS
# ===================================================================
results = {}
for key, sc in scenarios.items():
    print(f"  Solving: {sc['name']}...")
    sol = solve_dek(pi, sc["tau_hat"])
    results[key] = {**sc, **sol}
    welf_change = (sol["welfare"] - 1.0) * 100
    print(f"    Welfare change: median={np.median(welf_change):+.2f}%, "
          f"mean={np.mean(welf_change):+.2f}%, range=[{np.min(welf_change):+.1f}%, {np.max(welf_change):+.1f}%]")

# ===================================================================
# 6. COMPUTE TRILEMMA OUTCOMES PER SCENARIO
# ===================================================================
print("\nComputing trilemma outcomes...")

# GDI = 1 - HHI (computed from counterfactual trade shares)
# GSI = deployment speed (proxied by real income growth = welfare)
# GEI = developing-country share in global exports

def compute_trilemma(pi_scenario, welfare_change):
    """Compute GDI, GSI proxy, GEI from counterfactual trade shares"""
    # GDI per importing country
    hhi = (pi_scenario ** 2).sum(axis=0)
    gdi = 1.0 - hhi

    # GSI proxy: welfare change (consumption growth = deployment capacity)
    gsi = 1.0 + welfare_change  # baseline = 1.0

    # GEI: developing-country share in global exports
    dev_total = 0
    global_total = pi_scenario.sum(axis=1).sum()
    for i, c in enumerate(all_ctys):
        if c not in HIGH_INCOME:
            dev_total += pi_scenario[i, :].sum()
    gei = dev_total / max(global_total, 1e-10) if global_total > 0 else 0

    return {"gdi": gdi, "gsi": gsi, "gei": gei}

trilemma = {}
for key, res in results.items():
    # Counterfactual trade shares
    pi_cf = pi * res["pi_hat"]
    # Normalize: each column sums to 1
    pi_cf = pi_cf / pi_cf.sum(axis=0, keepdims=True)

    w_change = res["welfare"] - 1.0  # fractional change from baseline

    tl = compute_trilemma(pi_cf, w_change)
    trilemma[key] = tl

    # Summary stats
    gdi_mean = np.mean(tl["gdi"])
    gsi_mean = np.mean(tl["gsi"])
    gei_mean = tl["gei"]

    print(f"  {res['name']:30s}: GDI={gdi_mean:.3f}, GSI={gsi_mean:.3f}, GEI={gei_mean:.3f}")

# BAU as reference
bau = trilemma.get("S1_BAU", None)

# ===================================================================
# 7. SAVE RESULTS
# ===================================================================
print("\nSaving results...")

# Save scenario comparison
comparison = []
for key, res in results.items():
    tl = trilemma[key]
    w_change = res["welfare"] - 1.0
    gdi_mean = np.mean(tl["gdi"])
    gsi_mean = np.mean(tl["gsi"]) - 1.0  # deviation from 1.0

    # Relative to BAU
    if bau:
        gdi_delta = (np.mean(tl["gdi"]) - np.mean(bau["gdi"])) / max(np.mean(bau["gdi"]), 0.001) * 100
        gsi_delta = (np.mean(tl["gsi"]) - 1.0) * 100  # deviation from baseline
        gei_delta = (tl["gei"] - bau["gei"]) / max(bau["gei"], 0.001) * 100
    else:
        gdi_delta = gsi_delta = gei_delta = 0

    comparison.append({
        "scenario": res["name"],
        "welfare_change_pct": np.median(w_change) * 100,
        "gdi_mean": gdi_mean,
        "gdi_change_vs_bau_pct": gdi_delta if bau else 0,
        "gsi_change_pct": gsi_mean,
        "gei_global": tl["gei"],
        "gei_change_vs_bau_pct": gei_delta if bau else 0,
    })

comp_df = pd.DataFrame(comparison)
comp_path = os.path.join(PROC, "counterfactual_results.csv")
comp_df.to_csv(comp_path, index=False)
print(f"  Saved: {comp_path}")

# Save full welfare distribution
welfare_dist = {}
for key, res in results.items():
    welfare_dist[key] = {
        "name": res["name"],
        "welfare_pct_change": (res["welfare"] - 1.0).tolist(),
        "countries": all_ctys,
    }
welf_path = os.path.join(PROC, "welfare_distribution.json")
with open(welf_path, "w") as f:
    json.dump(welfare_dist, f)
print(f"  Saved: {welf_path}")

print("\nStructural model analysis complete.")
