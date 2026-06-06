#!/usr/bin/env python3
"""
Difference-in-Differences Estimation: De-risking Policy Effects
==============================================================
Implements staggered DID estimation for the Green Trade Trilemma paper.
Estimator: Two-way FE + Callaway-Sant'Anna dynamic effects.
Outcomes: import unit value (cost proxy), GDI, developing-country import share.
"""
import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "raw")
PROC = os.path.join(BASE, "data", "processed")
FIG_DIR = os.path.join(BASE, "figures_v13")
os.makedirs(FIG_DIR, exist_ok=True)

# ===================================================================
# 1. LOAD AND PREPARE DATA
# ===================================================================
print("=" * 70)
print("DID ESTIMATION: De-risking Policy Effects")
print("=" * 70)

# Load panel and policy with fixed country name mapping
from policy_mapping import load_and_fix_policy, build_policy_treatment_timing
panel = pd.read_csv(os.path.join(PROC, "panel_analysis_ready.csv"))
policy = load_and_fix_policy(RAW)

print(f"\nPanel: {len(panel):,} obs, {panel.country.nunique()} countries, "
      f"{int(panel.year.min())}-{int(panel.year.max())}")

# Build treatment timing with fixed country names
country_to_iso = panel[["country", "iso_code"]].drop_duplicates().set_index("country")["iso_code"].to_dict()
pcy = build_policy_treatment_timing(policy, country_to_iso)
panel = panel.merge(pcy[["iso_code", "first_treat_year"]], on="iso_code", how="left")
panel["first_treat_year"] = panel["first_treat_year"].fillna(0).astype(int)

print(f"\nPolicy events: {len(policy)}, {len(pcy)} treated countries")
print(f"Treatment years: {sorted(pcy.first_treat_year.unique())}")

# Treatment indicator
panel["treated"] = (panel["first_treat_year"] > 0).astype(int)
panel["post"] = ((panel["first_treat_year"] > 0) & (panel["year"] >= panel["first_treat_year"])).astype(int)

# Event time (relative to treatment)
panel["event_time"] = panel["year"] - panel["first_treat_year"]
panel.loc[panel["first_treat_year"] == 0, "event_time"] = -999

# ===================================================================
# 2. COMPUTE OUTCOME VARIABLES
# ===================================================================
print("\nComputing outcomes...")

# Outcome 1: Import cost proxy
# Load BACI country code mapping (numeric → ISO alpha-3)
import zipfile, io, csv as csv_mod
with zipfile.ZipFile(os.path.join(RAW, "BACI_HS12_V202601.zip"), 'r') as zf:
    cc_file = [n for n in zf.namelist() if 'country_codes' in n.lower()][0]
    with zf.open(cc_file) as f:
        text = io.TextIOWrapper(f, encoding='utf-8', errors='replace')
        reader = csv_mod.reader(text)
        next(reader)  # header
        code_map = {}
        for row in reader:
            if len(row) >= 4 and row[3]:
                code_map[int(row[0])] = row[3]  # numeric → ISO alpha-3
        text.detach()

# From BACI: compute unit value per importer-year
baci = pd.read_csv(os.path.join(RAW, "baci_low_carbon_trade.csv"))
baci = baci[baci["year"] >= 2015].copy()
baci["importer_iso3"] = baci["importer_iso"].map(code_map)
baci["exporter_iso3"] = baci["exporter_iso"].map(code_map)

# Unit value per importer-year (weighted by trade value)
baci_valid = baci[(baci["quantity_tons"] > 0) & (baci["value_kusd"] > 0)].copy()
baci_valid["unit_value"] = baci_valid["value_kusd"] / baci_valid["quantity_tons"]

# Weighted average unit value per importer-year
def weighted_avg(x):
    if x["quantity_tons"].sum() == 0:
        return np.nan
    return np.average(x["unit_value"], weights=x["value_kusd"])

import_cost = baci_valid.groupby(["importer_iso3", "year"]).apply(weighted_avg).reset_index()
import_cost.columns = ["iso_code", "year", "import_unit_value"]
import_cost["iso_code"] = import_cost["iso_code"].astype(str)
# Log transform for normality
import_cost["log_import_cost"] = np.log(import_cost["import_unit_value"].clip(lower=0.01))

# Merge to panel
panel = panel.merge(import_cost[["iso_code", "year", "log_import_cost", "import_unit_value"]],
                    on=["iso_code", "year"], how="left")

# Outcome 2: GDI (already in panel)
panel["gdi"].fillna(panel["gdi"].mean(), inplace=True)

# Outcome 3: Developing-country share in imports (country-level GEI, already in panel)
# This is the GEI index we just built

# ===================================================================
# 3. TWOWAY FIXED EFFECTS (BASELINE)
# ===================================================================
print("\n" + "=" * 70)
print("BASELINE: Two-way Fixed Effects")
print("=" * 70)

from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant

# Prepare regression data
reg_data = panel.dropna(subset=["log_import_cost", "gdi", "gei", "derisk_policy_index"]).copy()
reg_data["const"] = 1.0

# Create country and year dummies
country_dummies = pd.get_dummies(reg_data["iso_code"], prefix="cty", drop_first=True)
year_dummies = pd.get_dummies(reg_data["year"], prefix="yr", drop_first=True)

from statsmodels.api import OLS as OLS_sm

results = {}
for outcome, label in [("log_import_cost", "Import Cost (log)"),
                        ("gdi", "GDI (source diversity)"),
                        ("gei", "Dev-Country Import Share")]:
    y = reg_data[outcome].values
    X = pd.concat([
        reg_data[["derisk_policy_index"]],
        country_dummies,
        year_dummies,
    ], axis=1)
    # Add constant
    X = X.astype(float)

    try:
        model = OLS_sm(y, X, missing="drop").fit()
        beta = model.params["derisk_policy_index"]
        se = model.bse["derisk_policy_index"]
        pval = model.pvalues["derisk_policy_index"]
        n = len(y)
        results[outcome] = {"beta": beta, "se": se, "pval": pval, "n": n, "r2": model.rsquared}
        stars = "***" if pval < 0.01 else ("**" if pval < 0.05 else ("*" if pval < 0.1 else ""))
        print(f"  {label:30s}: beta={beta:+.4f}, se={se:.4f}, p={pval:.4f}{stars}, R2={model.rsquared:.3f}, N={n:,}")
    except Exception as e:
        print(f"  {label:30s}: ERROR - {e}")

# ===================================================================
# 4. DYNAMIC EVENT-STUDY (Callaway-Sant'Anna style)
# ===================================================================
print("\n" + "=" * 70)
print("EVENT-STUDY: Dynamic Treatment Effects")
print("=" * 70)

# For event study, we use the simple staggered design
# Event-time dummies for each outcome
event_times = sorted([t for t in panel["event_time"].unique()
                      if t >= -4 and t <= 4 and t != -999])

for outcome, label in [("log_import_cost", "Import cost (log)"),
                        ("gdi", "GDI"),
                        ("gei", "Dev-country import share")]:
    print(f"\n  --- {label} ---")

    # Build event-time dummies
    est_data = panel.dropna(subset=[outcome]).copy()

    # Bin event times outside [-4, 4]
    est_data["event_bin"] = est_data["event_time"].clip(-4, 4)

    event_dummies = pd.get_dummies(est_data["event_bin"], prefix="evt")
    # Drop evt_-1 (reference period, just before treatment)
    if "evt_-1" in event_dummies.columns:
        event_dummies = event_dummies.drop(columns=["evt_-1"])

    y = est_data[outcome].values
    X = pd.concat([
        event_dummies,
        pd.get_dummies(est_data["iso_code"], prefix="c", drop_first=True),
        pd.get_dummies(est_data["year"], prefix="y", drop_first=True),
    ], axis=1).astype(float)

    try:
        model = OLS_sm(y, X, missing="drop").fit()

        # Extract event-time coefficients
        coefs, ses, cis_low, cis_high = [], [], [], []
        times = []
        for t in sorted(est_data["event_bin"].unique()):
            col = f"evt_{t}"
            if col in model.params.index and t != -1:
                times.append(t)
                coefs.append(model.params[col])
                ses.append(model.bse[col])
                # 95% CI
                ci_lo = model.params[col] - 1.96 * model.bse[col]
                ci_hi = model.params[col] + 1.96 * model.bse[col]
                cis_low.append(ci_lo)
                cis_high.append(ci_hi)
                sig = "***" if model.pvalues[col] < 0.01 else ("**" if model.pvalues[col] < 0.05 else ("*" if model.pvalues[col] < 0.1 else ""))
                print(f"    t={t:3d}: coef={coefs[-1]:+.4f}, se={ses[-1]:.4f}, 95%CI=[{ci_lo:+.4f}, {ci_hi:+.4f}]{sig}")

        # Save for plotting
        results[f"es_{outcome}"] = {
            "times": times, "coefs": coefs, "ses": ses,
            "cis_low": cis_low, "cis_high": cis_high,
        }
    except Exception as e:
        print(f"    ERROR: {e}")

# ===================================================================
# 5. PLACEBO TEST
# ===================================================================
print("\n" + "=" * 70)
print("PLACEBO: Randomly reassigned treatment years")
print("=" * 70)

np.random.seed(42)
n_placebo = 100
placebo_betas = {k: [] for k in ["log_import_cost", "gdi", "gei"]}

# Get actual treated countries (ISO codes) and randomize their treatment years
treated_isos = pcy["iso_code"].unique()
actual_years = panel["year"].unique()

for i in range(n_placebo):
    # Randomly assign treatment years to treated countries
    placebo_treat = pd.DataFrame({
        "iso_code": treated_isos,
        "placebo_year": np.random.choice(actual_years, size=len(treated_isos), replace=True)
    })

    pnl = panel.copy()
    pnl = pnl.merge(placebo_treat, on="iso_code", how="left")
    pnl["placebo_year"] = pnl["placebo_year"].fillna(9999).astype(int)
    pnl["placebo_intensity"] = ((pnl["placebo_year"] <= pnl["year"]) & (pnl["placebo_year"] > 1900)).astype(float)

    for outcome in ["log_import_cost", "gdi", "gei"]:
        sub = pnl.dropna(subset=[outcome])
        if len(sub) < 50:
            continue
        y = sub[outcome].values
        X = pd.concat([
            sub[["placebo_intensity"]],
            pd.get_dummies(sub["iso_code"], prefix="c", drop_first=True),
            pd.get_dummies(sub["year"], prefix="y", drop_first=True),
        ], axis=1).astype(float)

        try:
            m = OLS_sm(y, X, missing="drop").fit()
            placebo_betas[outcome].append(m.params["placebo_intensity"])
        except:
            pass

print("Placebo distribution (should center on 0):")
for outcome, label in [("log_import_cost", "Import cost"),
                        ("gdi", "GDI"), ("gei", "Dev share")]:
    betas = placebo_betas[outcome]
    if betas:
        mean_b = np.mean(betas)
        sd_b = np.std(betas)
        sig_frac = np.mean([1 for b in betas if abs(b) > abs(results[outcome]["beta"])])
        print(f"  {label:20s}: placebo mean={mean_b:+.4f}(sd={sd_b:.4f}), "
              f"|β| > actual in {sig_frac:.1%} of draws")
        results[f"placebo_{outcome}"] = {"betas": betas}

# ===================================================================
# 6. HETEROGENEITY ANALYSIS
# ===================================================================
print("\n" + "=" * 70)
print("HETEROGENEITY: By income group and product category")
print("=" * 70)

# High vs low income
for group, group_label in [(1, "High-income"), (0, "Developing")]:
    sub = reg_data[reg_data["is_high_income"] == group]
    if len(sub) < 100:
        continue
    print(f"\n  {group_label} countries (N={len(sub)}):")
    for outcome, label in [("log_import_cost", "Cost"), ("gdi", "GDI"), ("gei", "Dev share")]:
        valid = sub.dropna(subset=[outcome])
        if len(valid) < 50:
            continue
        y = valid[outcome].values
        X = pd.concat([
            valid[["derisk_policy_index"]],
            pd.get_dummies(valid["iso_code"], prefix="c", drop_first=True),
            pd.get_dummies(valid["year"], prefix="y", drop_first=True),
        ], axis=1).astype(float)
        try:
            m = OLS_sm(y, X, missing="drop").fit()
            print(f"    {label:10s}: beta={m.params['derisk_policy_index']:+.4f}, se={m.bse['derisk_policy_index']:.4f}, p={m.pvalues['derisk_policy_index']:.4f}")
        except:
            pass

# ===================================================================
# 7. SAVE DETAILED RESULTS
# ===================================================================
print("\n" + "=" * 70)
print("RESULTS SUMMARY")
print("=" * 70)

for outcome, label in [("log_import_cost", "Import Cost Increase"),
                        ("gdi", "GDI Improvement"),
                        ("gei", "Dev-Country Import Share Change")]:
    if outcome in results:
        r = results[outcome]
        print(f"  {label:35s}: {r['beta']:+.4f} ({r['se']:.4f}), p={r['pval']:.4f}, N={r['n']:,}")

# Export results as CSV
summary_rows = []
for outcome, label in [("log_import_cost", "Import Cost (log)"),
                        ("gdi", "GDI"), ("gei", "Dev Import Share")]:
    if outcome in results:
        r = results[outcome]
        summary_rows.append({
            "outcome": label, "beta": r["beta"], "se": r["se"],
            "p_value": r["pval"], "n_obs": r["n"], "r_squared": r.get("r2", np.nan),
        })

summary_df = pd.DataFrame(summary_rows)
summary_path = os.path.join(PROC, "did_results_summary.csv")
summary_df.to_csv(summary_path, index=False)
print(f"\nSaved DID results to: {summary_path}")

# Save event-study coefficients
for outcome in ["log_import_cost", "gdi", "gei"]:
    key = f"es_{outcome}"
    if key in results:
        es = results[key]
        es_df = pd.DataFrame({
            "event_time": es["times"],
            "coefficient": es["coefs"],
            "se": es["ses"],
            "ci_lower": es["cis_low"],
            "ci_upper": es["cis_high"],
        })
        es_path = os.path.join(PROC, f"event_study_{outcome}.csv")
        es_df.to_csv(es_path, index=False)

print("\nDID analysis complete.")
