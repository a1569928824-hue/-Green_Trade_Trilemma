#!/usr/bin/env python3
"""
Figure 3: Causal Effects of De-risking Policies (Event-Study + DiD)
Nature journal standard. 3-panel event-study + robustness.
"""
import pandas as pd, numpy as np, os
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams.update({
    "figure.dpi": 72, "svg.fonttype": "none", "pdf.fonttype": 42,
    "font.family": "sans-serif", "font.sans-serif": ["Arial"],
    "font.size": 7.0, "axes.titlesize": 7.5, "axes.labelsize": 7.0,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5, "legend.fontsize": 6.0,
})

BASE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.join(BASE, "data", "processed")
RAW = os.path.join(BASE, "data", "raw")
FIG_DIR = os.path.join(BASE, "figures_v13")
os.makedirs(FIG_DIR, exist_ok=True)

# Load data
panel = pd.read_csv(os.path.join(PROC, "panel_analysis_ready.csv"))
from policy_mapping import load_and_fix_policy, build_policy_treatment_timing

policy = load_and_fix_policy(RAW)

# ===================================================================
# Build event-study with binary treatment (corrected via policy_mapping)
# ===================================================================
print("Running event-study for Figure 3...")

# Build treatment timing with fixed country names
country_to_iso = panel[["country", "iso_code"]].drop_duplicates().set_index("country")["iso_code"].to_dict()
pcy = build_policy_treatment_timing(policy, country_to_iso)
panel = panel.merge(pcy[["iso_code", "first_treat_year"]], on="iso_code", how="left")
panel["first_treat_year"] = panel["first_treat_year"].fillna(0).astype(int)
panel["event_time"] = panel["year"] - panel["first_treat_year"]
panel.loc[panel["first_treat_year"] == 0, "event_time"] = -999

# Binary post indicator
panel["post"] = ((panel["first_treat_year"] > 0) & (panel["year"] >= panel["first_treat_year"])).astype(int)

# Run event-study regressions with binned event times
from statsmodels.api import OLS

def run_event_study(outcome, data, event_range=(-4, 4)):
    sub = data.dropna(subset=[outcome]).copy()
    sub["event_bin"] = sub["event_time"].clip(event_range[0], event_range[1])

    evt_dummies = pd.get_dummies(sub["event_bin"], prefix="evt")
    if "evt_-1" in evt_dummies.columns:
        evt_dummies = evt_dummies.drop(columns=["evt_-1"])

    y = sub[outcome].values
    X = pd.concat([
        evt_dummies,
        pd.get_dummies(sub["iso_code"], prefix="c", drop_first=True),
        pd.get_dummies(sub["year"], prefix="y", drop_first=True),
    ], axis=1).astype(float)

    model = OLS(y, X, missing="drop").fit()

    times, coefs, ses, ci_lo, ci_hi = [], [], [], [], []
    for t in sorted(sub["event_bin"].unique()):
        col = f"evt_{t}"
        if col in model.params.index and t != -1:
            times.append(t)
            coefs.append(model.params[col])
            ses.append(model.bse[col])
            ci_lo.append(model.params[col] - 1.96 * model.bse[col])
            ci_hi.append(model.params[col] + 1.96 * model.bse[col])

    return {"times": np.array(times), "coefs": np.array(coefs), "ses": np.array(ses),
            "ci_lo": np.array(ci_lo), "ci_hi": np.array(ci_hi)}

# Compute unit costs from BACI
import io, zipfile, csv as csv_mod
with zipfile.ZipFile(os.path.join(RAW, "BACI_HS12_V202601.zip"), 'r') as zf:
    cc_file = [n for n in zf.namelist() if 'country_codes' in n.lower()][0]
    with zf.open(cc_file) as f:
        text = io.TextIOWrapper(f, encoding='utf-8', errors='replace')
        reader = csv_mod.reader(text)
        next(reader)
        code_map = {}
        for row in reader:
            if len(row) >= 4 and row[3]:
                code_map[int(row[0])] = row[3]
        text.detach()

baci = pd.read_csv(os.path.join(RAW, "baci_low_carbon_trade.csv"))
baci = baci[baci["year"] >= 2015].copy()
baci["importer_iso3"] = baci["importer_iso"].map(code_map)
baci_valid = baci[(baci["quantity_tons"] > 0) & (baci["value_kusd"] > 0)].copy()
baci_valid["unit_value"] = baci_valid["value_kusd"] / baci_valid["quantity_tons"]

def wavg(x):
    if x["quantity_tons"].sum() == 0:
        return np.nan
    return np.average(x["unit_value"], weights=x["value_kusd"])

import_cost = baci_valid.groupby(["importer_iso3", "year"]).apply(wavg).reset_index()
import_cost.columns = ["iso_code", "year", "import_unit_value"]
import_cost["log_cost"] = np.log(import_cost["import_unit_value"].clip(lower=0.01))
panel = panel.merge(import_cost[["iso_code", "year", "log_cost"]], on=["iso_code", "year"], how="left")

# Run event studies
es_cost = run_event_study("log_cost", panel)
es_gdi = run_event_study("gdi", panel)
es_gei = run_event_study("gei", panel)

# ===================================================================
# Plot
# ===================================================================
fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.0))
fig.subplots_adjust(left=0.08, right=0.96, top=0.90, bottom=0.15, wspace=0.35)

PANELS = [
    (axes[0], es_cost, "a  Import cost (log unit value)", "log points"),
    (axes[1], es_gdi, "b  Import source diversity (GDI)", "GDI (0--1)"),
    (axes[2], es_gei, "c  Dev.-country import share", "Share (0--1)"),
]

for ax, es, title, ylabel in PANELS:
    times = es["times"]
    coefs = es["coefs"]
    ci_lo = es["ci_lo"]
    ci_hi = es["ci_hi"]

    # Shaded area for post-treatment
    ax.axvspan(-0.5, max(times) + 0.5, alpha=0.06, color="red", zorder=0)

    # Reference line
    ax.axhline(y=0, color="black", linewidth=0.5, linestyle="--", zorder=1)

    # Confidence interval
    ax.fill_between(times, ci_lo, ci_hi, alpha=0.2, color="#377EB8", zorder=2)

    # Coefficient line
    ax.plot(times, coefs, color="#377EB8", linewidth=1.5, marker="o", markersize=4,
            markerfacecolor="white", markeredgewidth=1, zorder=3)

    # Vertical line at treatment
    ax.axvline(x=-0.5, color="red", linewidth=0.7, linestyle=":", zorder=1, alpha=0.7)

    ax.set_xlabel("Years since policy implementation", fontsize=6.5)
    ax.set_ylabel(ylabel, fontsize=6.5)
    ax.set_title(title, loc="left", fontsize=7.5, fontweight="bold")

    # Tick formatting
    ax.set_xticks(range(int(min(times)), int(max(times)) + 1))
    ax.tick_params(labelsize=6)

# Suptitle
fig.suptitle("Causal Effects of De-risking Policies on Clean-Tech Outcomes",
             fontsize=8.5, fontweight="bold", y=0.97)

# Note
fig.text(0.5, 0.02, "Event-study estimates with 95% CI. Country and year fixed effects included. "
         "Reference period: t = -1.",
         ha="center", fontsize=5.5, fontstyle="italic")

# Save
for fmt, ext in [("svg", ".svg"), ("pdf", ".pdf"), ("tiff", ".tiff")]:
    out_path = os.path.join(FIG_DIR, f"Fig3_event_study{ext}")
    if fmt == "tiff":
        fig.savefig(out_path, dpi=600, format="tiff", pil_kwargs={"compression": "tiff_lzw"})
    else:
        fig.savefig(out_path, dpi=300, format=fmt, bbox_inches="tight")
    print(f"  Saved: {out_path}")

print("Figure 3 done.")
