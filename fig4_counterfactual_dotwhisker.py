#!/usr/bin/env python3
"""
Figure 4 — Dot-whisker plot of counterfactual scenario outcomes.
Replaces the heatmap (Fig4) with a more precise and Nature-standard format.
"""
import pandas as pd, numpy as np, os
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "figure.dpi": 72,
    "font.size": 7.0,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.linewidth": 0.7,
    "legend.frameon": False,
    "xtick.major.width": 0.7,
    "ytick.major.width": 0.7,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "axes.labelsize": 7.0,
    "legend.fontsize": 6.0,
})

C_SPEED = "#D45D2C"
C_DIVER = "#2C6E8F"
C_EQUITY = "#3A7D4A"
C_DARK = "#272727"
C_NEUTRAL = "#767676"

BASE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.join(BASE, "data", "processed")
FIG_DIR = os.path.join(BASE, "figures_v13")
os.makedirs(FIG_DIR, exist_ok=True)

cf = pd.read_csv(os.path.join(PROC, "counterfactual_results.csv"))
scenarios_plot = cf[cf["scenario"] != "Business as Usual"].copy()

short_names = {
    "Full Decoupling from China": "Full Decoupling",
    "CBAM Extension": "CBAM Extension",
    "Climate Club (G7+China)": "Climate Club\n(G7+China)",
    "Inclusive Green Trade": "Inclusive\nGreen Trade",
    "China Export Restrictions": "China Export\nRestrictions",
}

outcomes = [
    ("gsi_change_pct", "Decarbonization Speed\n(% change from BAU)", C_SPEED),
    ("gdi_change_vs_bau_pct", "Supply Chain Diversity\n(GDI, % change from BAU)", C_DIVER),
    ("gei_change_vs_bau_pct", "Developing-Country\nExport Share (GEI, % change)", C_EQUITY),
]

fig, axes = plt.subplots(1, 3, figsize=(7.5, 3.8))
fig.subplots_adjust(left=0.08, right=0.96, top=0.90, bottom=0.12, wspace=0.36)

scenario_labels = [short_names.get(s, s[:25]) for s in scenarios_plot["scenario"]]

for ax, (col, title, color) in zip(axes, outcomes):
    vals = scenarios_plot[col].values
    labels = scenario_labels

    y_positions = range(len(labels))
    ax.scatter(vals, y_positions, s=50, color=color, zorder=3, edgecolors="white", linewidth=0.5)
    ax.hlines(y_positions, 0, vals, colors=color, linewidth=2.5, alpha=0.7, zorder=2)

    ax.axvline(0, color=C_NEUTRAL, linewidth=0.6, linestyle="--", zorder=1, alpha=0.5)

    for i, (val, label) in enumerate(zip(vals, labels)):
        sign = "+" if val > 0 else ""
        text_x = val + (0.8 if val >= 0 else -0.8)
        ha = "left" if val >= 0 else "right"
        ax.text(text_x, i, f"{sign}{val:.1f}%", fontsize=6.5, ha=ha, va="center",
                color=C_DARK, fontweight="bold")

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels, fontsize=6.5)
    ax.set_xlabel(title, fontsize=6.5, color=C_DARK)
    ax.set_title(title.split("\n")[0], loc="left", fontsize=7.5, fontweight="bold", color=C_DARK)
    ax.tick_params(labelsize=6)
    ax.set_ylim(-0.8, len(labels) - 0.2)
    ax.invert_yaxis()

# Highlight the best overall scenario
fig.suptitle("Counterfactual Policy Outcomes: Structural Model Results",
             fontsize=8.5, fontweight="bold", y=0.98, color=C_DARK)
fig.text(0.5, 0.01, "Percentage change relative to Business-as-Usual baseline. "
         "DEK exact-hat algebra, theta = 4.2. N = 40 countries.",
         ha="center", fontsize=5.5, fontstyle="italic", color=C_NEUTRAL)

for fmt, ext in [("svg", ".svg"), ("pdf", ".pdf"), ("tiff", ".tiff")]:
    out_path = os.path.join(FIG_DIR, f"Fig4_counterfactual_dotwhisker{ext}")
    if fmt == "tiff":
        fig.savefig(out_path, dpi=600, format="tiff", pil_kwargs={"compression": "tiff_lzw"})
    else:
        fig.savefig(out_path, dpi=300, format=fmt, bbox_inches="tight")
    print(f"  Saved: {out_path}")

print("Figure 4 (dot-whisker counterfactuals) done.")
