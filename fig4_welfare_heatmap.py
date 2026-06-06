#!/usr/bin/env python3
"""
Figure 4: Welfare Decomposition Across Counterfactual Scenarios
Nature-standard heatmap showing % change vs BAU in 3 trilemma dimensions.
"""
import pandas as pd, numpy as np, os
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

mpl.rcParams.update({
    "figure.dpi": 72, "svg.fonttype": "none", "pdf.fonttype": 42,
    "font.family": "sans-serif", "font.sans-serif": ["Arial"],
    "font.size": 7.0, "axes.titlesize": 7.5, "axes.labelsize": 7.0,
    "xtick.labelsize": 6.5, "ytick.labelsize": 6.5,
})

BASE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.join(BASE, "data", "processed")
FIG_DIR = os.path.join(BASE, "figures_v13")
os.makedirs(FIG_DIR, exist_ok=True)

# Load counterfactual results
cf = pd.read_csv(os.path.join(PROC, "counterfactual_results.csv"))
print("Loaded counterfactual results:")
print(cf.to_string())

# ===================================================================
# Build heatmap data
# ===================================================================
# Scenarios (rows) — exclude BAU
scenarios_plot = cf[cf["scenario"] != "Business as Usual"].copy()
scenario_names = {
    "Full Decoupling from China": "Full\nDecoupling",
    "CBAM Extension": "CBAM\nExtension",
    "Climate Club (G7+China)": "Climate\nClub",
    "Inclusive Green Trade": "Inclusive\nGreen Trade",
    "China Export Restrictions": "China\nExport\nRestrict.",
}

# Outcomes (columns)
outcomes = [
    ("gsi_change_pct", "Decarbonization\nSpeed"),
    ("gdi_change_vs_bau_pct", "Supply Chain\nDiversity (GDI)"),
    ("gei_change_vs_bau_pct", "Dev.-Country\nExport Share (GEI)"),
]

# Build matrix
M = np.zeros((len(scenarios_plot), len(outcomes)))
annotations = []
for i, (_, row) in enumerate(scenarios_plot.iterrows()):
    for j, (col, _) in enumerate(outcomes):
        M[i, j] = row[col]
    annotations.append([f"{row[col]:+.1f}%" for col, _ in outcomes])

# ===================================================================
# Plot
# ===================================================================
fig, ax = plt.subplots(figsize=(5.0, 3.5))
fig.subplots_adjust(left=0.22, right=0.95, top=0.92, bottom=0.12)

# Custom colormap: blue (improvement) - white (neutral) - red (deterioration)
cmap = LinearSegmentedColormap.from_list("diverge",
    [(0.0, "#2166AC"), (0.35, "#92C5DE"), (0.5, "#F7F7F7"),
     (0.65, "#F4A582"), (1.0, "#B2182B")])

vmax = max(abs(M.min()), abs(M.max()), 30)
im = ax.imshow(M, cmap=cmap, aspect="auto", vmin=-vmax, vmax=vmax)

# Annotations
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        val = M[i, j]
        text_color = "white" if abs(val) > vmax * 0.6 else "black"
        ax.text(j, i, f"{val:+.1f}%", ha="center", va="center",
                fontsize=8, fontweight="bold", color=text_color)

# Axes
scenario_labels = [scenario_names.get(s, s[:20]) for s in scenarios_plot["scenario"]]
ax.set_yticks(range(len(scenario_labels)))
ax.set_yticklabels(scenario_labels, fontsize=7)
ax.set_xticks(range(len(outcomes)))
ax.set_xticklabels([o[1] for o in outcomes], fontsize=7)
ax.xaxis.set_ticks_position("top")
ax.xaxis.set_label_position("top")

# Colorbar
cbar = fig.colorbar(im, ax=ax, orientation="horizontal", pad=0.12, shrink=0.8)
cbar.set_label("% Change from Business-as-Usual", fontsize=6.5)
cbar.ax.tick_params(labelsize=6)

# Title
ax.set_title("Welfare Decomposition: Counterfactual Policy Scenarios",
            fontsize=9, fontweight="bold", pad=12)

# Note
fig.text(0.5, 0.01, "Positive = improvement over BAU. BAU = current policy trends through 2035. "
         "DEK exact-hat model, theta=4.2.",
         ha="center", fontsize=5.5, fontstyle="italic")

# Save
for fmt, ext in [("svg", ".svg"), ("pdf", ".pdf"), ("tiff", ".tiff")]:
    out_path = os.path.join(FIG_DIR, f"Fig4_welfare_heatmap{ext}")
    if fmt == "tiff":
        fig.savefig(out_path, dpi=600, format="tiff", pil_kwargs={"compression": "tiff_lzw"})
    else:
        fig.savefig(out_path, dpi=300, format=fmt, bbox_inches="tight")
    print(f"  Saved: {out_path}")

print("Figure 4 done.")
