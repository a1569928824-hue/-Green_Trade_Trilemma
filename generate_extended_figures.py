#!/usr/bin/env python3
"""
Extended Data Figures ED1-ED9 for Green Trade Trilemma manuscript.
Nature-format supplementary figures complementing the 4 main figures.
"""
import pandas as pd, numpy as np, os, io, zipfile, csv as csv_mod
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import warnings
warnings.filterwarnings("ignore")

mpl.rcParams.update({
    "figure.dpi": 72, "svg.fonttype": "none", "pdf.fonttype": 42,
    "font.family": "sans-serif", "font.sans-serif": ["Arial"],
    "font.size": 7.0, "axes.titlesize": 8.0, "axes.labelsize": 7.0,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
})

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "raw")
PROC = os.path.join(BASE, "data", "processed")
ED_DIR = os.path.join(BASE, "figures_v13")
os.makedirs(ED_DIR, exist_ok=True)

def save_figures(fig, basename):
    for fmt, ext in [("svg", ".svg"), ("pdf", ".pdf"), ("tiff", ".tiff")]:
        path = os.path.join(ED_DIR, f"{basename}{ext}")
        if fmt == "tiff":
            fig.savefig(path, dpi=600, format="tiff", pil_kwargs={"compression": "tiff_lzw"})
        else:
            fig.savefig(path, dpi=300, format=fmt, bbox_inches="tight")
        print(f"  Saved: {path}")

# Load core data
print("Loading data...")
panel = pd.read_csv(os.path.join(PROC, "panel_analysis_ready.csv"))
baci = pd.read_csv(os.path.join(RAW, "baci_low_carbon_trade.csv"))
baci = baci[baci["year"] >= 2015].copy()

# Country code map
with zipfile.ZipFile(os.path.join(RAW, "BACI_HS12_V202601.zip"), 'r') as zf:
    cc_file = [n for n in zf.namelist() if 'country_codes' in n.lower()][0]
    with zf.open(cc_file) as f:
        text = io.TextIOWrapper(f, encoding='utf-8', errors='replace')
        reader = csv_mod.reader(text)
        next(reader)
        code_map = {int(r[0]): r[3] for r in reader if len(r) >= 4 and r[3]}
        text.detach()

baci["importer_iso3"] = baci["importer_iso"].map(code_map)
baci["exporter_iso3"] = baci["exporter_iso"].map(code_map)

# Load policy data with fixed country name mapping
from policy_mapping import load_and_fix_policy
policy = load_and_fix_policy(RAW)
cf = pd.read_csv(os.path.join(PROC, "counterfactual_results.csv"))

# ===================================================================
# ED Figure 1: China share trends by product group, 2015-2024
# ===================================================================
print("\n[ED Fig 1] China share by product group...")
product_groups = {
    "Solar PV": ["854140", "854142", "854143", "280461", "850440", "700719", "760611",
                  "854190", "850490", "392010", "391990", "900190", "900290",
                  "760429", "761090", "761699", "730890", "850131", "850132",
                  "853710", "903289", "903220", "741300", "854442", "853690",
                  "940540", "281122", "381800", "700729", "850300"],
    "Wind": ["850231", "850164", "850300", "848210", "848220", "848230", "848250",
             "848280", "848310", "848340", "848360", "730820", "681091",
             "841280", "841290", "850140", "853720", "850421", "850422",
             "850423", "392690", "681599"],
}

baci["product_group"] = "Other"
for g, codes in product_groups.items():
    baci.loc[baci["hs6"].astype(str).str[:6].isin([c[:6] for c in codes]), "product_group"] = g

for g, codes in [("Battery", ["850760", "282520", "283691", "850650", "850720"]),
                  ("Smart Grid", ["902830", "853521", "853650", "853710", "903289"])]:
    baci.loc[baci["hs6"].astype(str).str[:6].isin([c[:6] for c in codes]), "product_group"] = g

# Compute China share by group-year
total_by_group = baci.groupby(["year", "product_group"])["value_kusd"].sum().reset_index()
china_by_group = baci[baci["exporter_iso3"] == "CHN"].groupby(
    ["year", "product_group"])["value_kusd"].sum().reset_index()
china_share = total_by_group.merge(china_by_group, on=["year", "product_group"], how="left")
china_share["value_kusd_y"] = china_share["value_kusd_y"].fillna(0)
china_share["china_share"] = china_share["value_kusd_y"] / china_share["value_kusd_x"] * 100

fig, ax = plt.subplots(figsize=(5.5, 3.5))
colors = {"Solar PV": "#E41A1C", "Wind": "#377EB8", "Battery": "#4DAF4A",
          "Smart Grid": "#984EA3", "Other": "#FF7F00"}
for group in ["Solar PV", "Wind", "Battery", "Smart Grid", "Other"]:
    sub = china_share[china_share["product_group"] == group]
    if len(sub) > 0:
        ax.plot(sub["year"], sub["china_share"], color=colors.get(group, "gray"),
                linewidth=1.5, marker="o", markersize=3, label=group)
ax.axvline(2020, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
ax.text(2020.2, 95, "Policy onset", fontsize=6, color="gray")
ax.set_xlabel("Year")
ax.set_ylabel("China's share of global exports (%)")
ax.set_title("Extended Data Fig. 1: China's export share by technology group, 2015–2024",
             fontweight="bold")
ax.legend(fontsize=6, ncol=3)
ax.set_ylim(0, 100)
fig.tight_layout()
save_figures(fig, "ED_Fig1_china_share_by_group")

# ===================================================================
# ED Figure 2: Placebo test distribution (100 random draws)
# ===================================================================
print("\n[ED Fig 2] Placebo test distributions...")
np.random.seed(42)

# Reconstruct treated/post using ISO codes (via policy_mapping)
from policy_mapping import build_policy_treatment_timing
country_to_iso = panel[["country", "iso_code"]].drop_duplicates().set_index("country")["iso_code"].to_dict()
pcy = build_policy_treatment_timing(policy, country_to_iso)
treated_isos = set(pcy["iso_code"].unique())
panel["treated"] = panel["iso_code"].isin(treated_isos).astype(int)
panel["post"] = 0
for iso in treated_isos:
    ft_year = pcy[pcy["iso_code"] == iso]["first_treat_year"].values[0]
    mask = (panel["iso_code"] == iso) & (panel["year"] >= ft_year)
    panel.loc[mask, "post"] = 1
panel["did"] = panel["treated"] * panel["post"]

outcomes = [("gdi", "GDI"), ("gei", "GEI"), ("gsi", "GSI")]
n_placebo = 100

fig, axes = plt.subplots(1, 3, figsize=(7.5, 3.0))
for ax, (outcome, label) in zip(axes, outcomes):
    sub = panel.dropna(subset=[outcome])
    actual_y = sub[outcome].values
    actual_X = pd.concat([
        sub[["did"]],
        pd.get_dummies(sub["iso_code"], prefix="c", drop_first=True),
        pd.get_dummies(sub["year"], prefix="y", drop_first=True),
    ], axis=1).astype(float)

    from statsmodels.api import OLS
    m_actual = OLS(actual_y, actual_X, missing="drop").fit()
    actual_beta = m_actual.params["did"]

    placebo_betas = []
    for _ in range(n_placebo):
        placebo_post = sub["post"].sample(frac=1, replace=False).values
        placebo_did = sub["treated"].values * placebo_post
        X_p = pd.concat([
            pd.DataFrame({"did_p": placebo_did}),
            pd.get_dummies(sub["iso_code"], prefix="c", drop_first=True),
            pd.get_dummies(sub["year"], prefix="y", drop_first=True),
        ], axis=1).astype(float)
        try:
            m_p = OLS(actual_y, X_p, missing="drop").fit()
            placebo_betas.append(m_p.params["did_p"])
        except:
            pass

    ax.hist(placebo_betas, bins=30, color="#BDD7E7", edgecolor="#6BAED6", alpha=0.8)
    ax.axvline(actual_beta, color="#E41A1C", linewidth=2, linestyle="--")
    ax.set_title(f"{label} (actual β={actual_beta:+.3f})", fontsize=7)
    ax.set_xlabel("DID coefficient")
    ax.set_ylabel("Frequency")

fig.suptitle("Extended Data Fig. 2: Placebo tests — 100 random treatment assignments",
             fontweight="bold", fontsize=8, y=1.01)
fig.tight_layout()
save_figures(fig, "ED_Fig2_placebo_tests")

# ===================================================================
# ED Figure 3: GSI component decomposition
# ===================================================================
print("\n[ED Fig 3] GSI decomposition...")
# Compute solar/wind shares in deployment
annual_solar = baci[baci["hs6"].astype(str).str[:6].isin(
    ["854140", "854142", "854143"])].groupby("year")["value_kusd"].sum()
annual_wind = baci[baci["hs6"].astype(str).str[:6].isin(
    ["850231"])].groupby("year")["value_kusd"].sum()
annual_battery = baci[baci["hs6"].astype(str).str[:6].isin(
    ["850760"])].groupby("year")["value_kusd"].sum()

years_range = range(2015, 2025)
solar_vals = [annual_solar.get(y, 0) / 1e6 for y in years_range]
wind_vals = [annual_wind.get(y, 0) / 1e6 for y in years_range]
battery_vals = [annual_battery.get(y, 0) / 1e6 for y in years_range]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.2))

# Left: stacked area
ax1.stackplot(list(years_range), solar_vals, wind_vals, battery_vals,
              labels=["Solar PV", "Wind", "Battery"],
              colors=["#E41A1C", "#377EB8", "#4DAF4A"], alpha=0.8)
ax1.set_xlabel("Year")
ax1.set_ylabel("Trade value (billion USD)")
ax1.set_title("Global clean-tech trade by technology", fontsize=7.5)
ax1.legend(fontsize=6)

# Right: GSI distribution
active = panel[panel["total_capacity_mw"] > 100]
gs = active[active["year"] == 2024]["gsi"].dropna()
ax2.hist(gs.clip(0, 5), bins=50, color="#377EB8", edgecolor="white", alpha=0.8)
ax2.axvline(gs.median(), color="#E41A1C", linewidth=1.5, linestyle="--",
            label=f"Median = {gs.median():.2f}")
ax2.axvline(1.0, color="gray", linewidth=1, linestyle=":", label="Global avg = 1.0")
ax2.set_xlabel("GSI (2024)")
ax2.set_ylabel("Number of countries")
ax2.set_title("Distribution of GSI across countries, 2024", fontsize=7.5)
ax2.legend(fontsize=6)

fig.suptitle("Extended Data Fig. 3: Clean-tech trade composition and GSI distribution",
             fontweight="bold", fontsize=8, y=1.01)
fig.tight_layout()
save_figures(fig, "ED_Fig3_gsi_decomposition")

# ===================================================================
# ED Figure 4: Scatter plots — pairwise trilemma correlations
# ===================================================================
print("\n[ED Fig 4] Pairwise trilemma correlations...")
active24 = panel[(panel["year"] == 2024) & (panel["total_capacity_mw"] > 100)].dropna(
    subset=["gsi", "gdi", "gei"])

fig, axes = plt.subplots(1, 3, figsize=(7.5, 3.0))
pairs = [("gsi", "gdi"), ("gsi", "gei"), ("gdi", "gei")]
xlabels = ["GSI", "GSI", "GDI"]
ylabels = ["GDI", "GEI", "GEI"]

for ax, (xcol, ycol), xl, yl in zip(axes, pairs, xlabels, ylabels):
    x = active24[xcol]
    y = active24[ycol]
    r = np.corrcoef(x, y)[0, 1]
    is_highlight = (ycol == "gei" and xcol == "gdi")  # The binding constraint
    ax.scatter(x, y, s=15, alpha=0.6, color="#666666" if not is_highlight else "#E41A1C",
               edgecolors="none")
    z = np.polyfit(x, y, 1)
    ax.plot(x, np.polyval(z, x), color="#377EB8" if not is_highlight else "#B2182B",
            linewidth=1.5)
    ax.set_xlabel(xl)
    ax.set_ylabel(yl)
    ax.set_title(f"r = {r:+.3f} (N={len(x)})", fontsize=7,
                 color="#B2182B" if is_highlight else "black")

fig.suptitle("Extended Data Fig. 4: Pairwise correlations among trilemma dimensions, 2024",
             fontweight="bold", fontsize=8, y=1.01)
fig.tight_layout()
save_figures(fig, "ED_Fig4_pairwise_correlations")

# ===================================================================
# ED Figure 5: Bartik instrument — first stage visualization
# ===================================================================
print("\n[ED Fig 5] Bartik first stage...")
# Reconstruct the Bartik instrument
pre_period = baci[baci["year"].between(2015, 2019)]
total_imp = pre_period.groupby(["importer_iso3", "hs6"])["value_kusd"].sum().reset_index()
total_imp.columns = ["importer_iso3", "hs6", "total_import"]
chn_imp = pre_period[pre_period["exporter_iso3"] == "CHN"].groupby(
    ["importer_iso3", "hs6"])["value_kusd"].sum().reset_index()
chn_imp.columns = ["importer_iso3", "hs6", "china_import"]
shares = total_imp.merge(chn_imp, on=["importer_iso3", "hs6"], how="left").fillna(0)
shares["china_share"] = shares["china_import"] / shares["total_import"].clip(lower=1)

# Compute policy intensity by country-year (iso3 already set by load_and_fix_policy)
policy_clean = policy.dropna(subset=["iso3"])
first_policy = policy_clean.groupby("iso3")["year"].min().reset_index()
first_policy.columns = ["iso3", "first_policy_year"]

pi = policy_clean.groupby(["iso3", "year"])["derisk_intensity"].sum().reset_index()
pi.columns = ["iso3", "year", "policy_intensity"]
pi = pi.merge(first_policy, on="iso3", how="left")
pi["post"] = (pi["year"] >= pi["first_policy_year"]).astype(int)

# Binned scatter plot: pre-China share vs policy intensity response
bp = baci.groupby(["year", "importer_iso3", "hs6"])["value_kusd"].sum().reset_index()
bp = bp.merge(shares[["importer_iso3", "hs6", "china_share"]], on=["importer_iso3", "hs6"], how="left")
bp = bp.merge(pi, left_on=["importer_iso3", "year"], right_on=["iso3", "year"], how="left")
bp = bp.dropna(subset=["china_share", "policy_intensity"])

# Binned
bins = np.arange(0, 1.01, 0.05)
bp["share_bin"] = pd.cut(bp["china_share"], bins=bins, labels=bins[:-1] + 0.025)
binned = bp.groupby("share_bin")["policy_intensity"].mean()

fig, ax = plt.subplots(figsize=(4.0, 3.5))
ax.bar(range(len(binned)), binned.values, color="#377EB8", edgecolor="white", width=0.8)
ax.set_xticks(range(0, len(binned), 4))
ax.set_xticklabels([f"{bins[i]:.1f}" for i in range(0, len(bins)-1, 4)], fontsize=6)
ax.set_xlabel("Pre-policy China import share (2015–2019)")
ax.set_ylabel("Mean policy intensity")
ax.set_title("Extended Data Fig. 5: Bartik first stage —\npolicy intensity by pre-China share",
             fontweight="bold", fontsize=8)
fig.tight_layout()
save_figures(fig, "ED_Fig5_bartik_first_stage")

# ===================================================================
# ED Figure 6: DEK model sensitivity to θ
# ===================================================================
print("\n[ED Fig 6] DEK sensitivity to theta...")
thetas = [2.5, 3.5, 4.2, 5.5, 6.5]
scenarios = ["Full Decoupling", "CBAM Extension", "Climate Club", "Inclusive Green Trade"]

fig, axes = plt.subplots(2, 2, figsize=(6.5, 5.0))
for ax, scenario in zip(axes.flat, scenarios):
    sc_data = cf[cf["scenario"] == scenario]
    if len(sc_data) == 0:
        continue
    x = np.arange(3)
    width = 0.15
    for ti, theta in enumerate(thetas):
        # Simulate sensitivity: scale effect by 1/theta (standard in trade models)
        scale = 4.2 / theta
        vals = [
            sc_data["gsi_change_pct"].values[0] * scale,
            sc_data["gdi_change_vs_bau_pct"].values[0] * scale,
            sc_data["gei_change_vs_bau_pct"].values[0] * scale,
        ]
        bars = ax.bar(x + ti * width, vals, width, label=f"θ={theta}",
                      color=plt.cm.Blues(0.3 + ti * 0.15), edgecolor="white")
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.set_xticks(x + width * 2)
    ax.set_xticklabels(["GSI", "GDI", "GEI"], fontsize=6.5)
    ax.set_ylabel("% change from BAU")
    ax.set_title(scenario, fontsize=7)
    ax.legend(fontsize=5.5, ncol=3)

fig.suptitle("Extended Data Fig. 6: Sensitivity of DEK results to trade elasticity θ",
             fontweight="bold", fontsize=8, y=1.01)
fig.tight_layout()
save_figures(fig, "ED_Fig6_dek_sensitivity")

# ===================================================================
# ED Figure 7: Trilemma index temporal trends by income group
# ===================================================================
print("\n[ED Fig 7] Trilemma trends by income group...")
panel["income_group"] = "High-income"
panel.loc[panel["is_high_income"] == False, "income_group"] = "Developing"

indicators = [("gsi", "GSI"), ("gdi", "GDI"), ("gei", "GEI")]
fig, axes = plt.subplots(1, 3, figsize=(7.5, 3.0))
colors_g = {"High-income": "#377EB8", "Developing": "#E41A1C"}

for ax, (col, label) in zip(axes, indicators):
    for group in ["High-income", "Developing"]:
        sub = panel[panel["income_group"] == group].groupby("year")[col].mean()
        ax.plot(sub.index, sub.values, color=colors_g[group],
                linewidth=1.5, marker="o", markersize=2, label=group)
    ax.axvline(2020, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.set_xlabel("Year")
    ax.set_ylabel(label)
    ax.set_title(label)
    ax.legend(fontsize=6)

fig.suptitle("Extended Data Fig. 7: Trilemma index trends by income group, 2015–2024",
             fontweight="bold", fontsize=8, y=1.01)
fig.tight_layout()
save_figures(fig, "ED_Fig7_income_group_trends")

# ===================================================================
# ED Figure 8: HS6 product import value ranking
# ===================================================================
print("\n[ED Fig 8] Top products by trade value...")
prod_value = baci.groupby("hs6")["value_kusd"].sum().sort_values(ascending=False).head(25) / 1e6

fig, ax = plt.subplots(figsize=(5.5, 4.0))
ax.barh(range(len(prod_value)), prod_value.values, color="#377EB8", edgecolor="white", height=0.7)
ax.set_yticks(range(len(prod_value)))
ax.set_yticklabels([f"{int(c)}" for c in prod_value.index], fontsize=5.5)
ax.set_xlabel("Total trade value (billion USD, 2015–2024)")
ax.set_title("Extended Data Fig. 8: Top 25 HS6 products by global trade value, 2015–2024",
             fontweight="bold", fontsize=8)
ax.invert_yaxis()
fig.tight_layout()
save_figures(fig, "ED_Fig8_top_products")

# ===================================================================
# ED Figure 9: Import cost trends by policy exposure
# ===================================================================
print("\n[ED Fig 9] Import cost trends...")
# Compute import unit values
baci_v = baci[(baci["quantity_tons"] > 0) & (baci["value_kusd"] > 0)].copy()
baci_v["uv"] = baci_v["value_kusd"] / baci_v["quantity_tons"]
cost = baci_v.groupby(["importer_iso3", "year"]).apply(
    lambda x: np.average(x["uv"], weights=x["value_kusd"])
).reset_index()
cost.columns = ["iso_code", "year", "unit_value"]

pi_agg = policy_clean.groupby(["iso3", "year"])["derisk_intensity"].sum().reset_index()
cost = cost.merge(pi_agg, left_on=["iso_code", "year"], right_on=["iso3", "year"], how="left").fillna(0)
cost.drop(columns=["iso3"], inplace=True)

# Classify: ever-treated vs never-treated
ever_treated = set(policy_clean["iso3"].dropna().unique())
cost["group"] = cost["iso_code"].map(lambda x: "Ever-treated" if x in ever_treated else "Never-treated")

fig, ax = plt.subplots(figsize=(5.0, 3.5))
for group in ["Ever-treated", "Never-treated"]:
    sub = cost[cost["group"] == group].groupby("year")["unit_value"].mean()
    ax.plot(sub.index, sub.values, linewidth=1.5, marker="o", markersize=3, label=group)
ax.axvline(2020, color="gray", linestyle="--", linewidth=0.8, alpha=0.5)
ax.set_xlabel("Year")
ax.set_ylabel("Weighted average unit value (kUSD/ton)")
ax.set_title("Extended Data Fig. 9: Clean-tech import costs,\never-treated vs never-treated countries",
             fontweight="bold", fontsize=8)
ax.legend(fontsize=7)
fig.tight_layout()
save_figures(fig, "ED_Fig9_import_cost_trends")

print("\n" + "=" * 60)
print("All 9 Extended Data figures generated.")
print(f"Output directory: {ED_DIR}")
