#!/usr/bin/env python3
"""
Figure 5 — Temporal evolution of the trilemma by income group, 2015-2024.
Nature-quality 3-panel time-series line plot.
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

C_HI = "#2C6E8F"
C_DEV = "#D45D2C"
C_DARK = "#272727"
C_NEUTRAL = "#767676"

BASE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.join(BASE, "data", "processed")
FIG_DIR = os.path.join(BASE, "figures_v13")
os.makedirs(FIG_DIR, exist_ok=True)

panel = pd.read_csv(os.path.join(PROC, "panel_analysis_ready.csv"))
panel["income_group"] = "High-income"
panel.loc[panel["is_high_income"] == False, "income_group"] = "Developing"

indicators = [
    ("gsi", "GSI (Green Speed Index)", "Renewable deployment speed\n(relative to global average, 2015 = 1.0)"),
    ("gdi", "GDI (Green Diversity Index)", "Import source diversity\n(1 - HHI, higher = more diverse)"),
    ("gei", "GEI (Green Equity Index)", "Share of imports from\ndeveloping countries"),
]

fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.8))
fig.subplots_adjust(left=0.07, right=0.97, top=0.88, bottom=0.15, wspace=0.38)

for ax, (col, title, ylabel) in zip(axes, indicators):
    for group, color, ls in [("High-income", C_HI, "-"), ("Developing", C_DEV, "--")]:
        sub = panel[panel["income_group"] == group].groupby("year")[col].mean()
        ax.plot(sub.index, sub.values, color=color, linewidth=1.5, linestyle=ls,
                marker="o", markersize=3, markerfacecolor="white", markeredgewidth=1,
                markeredgecolor=color, label=group)

    ax.axvline(2020, color=C_NEUTRAL, linestyle=":", linewidth=0.8, alpha=0.6)
    ax.text(2020.2, ax.get_ylim()[1] * 0.98, "Policy onset", fontsize=5.5, color=C_NEUTRAL,
            va="top")

    ax.set_xlabel("Year")
    ax.set_ylabel(ylabel, fontsize=6)
    ax.set_title(title, loc="left", fontsize=7.5, fontweight="bold", color=C_DARK)
    ax.set_xlim(2014.5, 2024.5)
    ax.legend(fontsize=6, loc="best")
    ax.tick_params(labelsize=6)

fig.suptitle("Temporal Evolution of the Green Trade Trilemma by Income Group",
             fontsize=8.5, fontweight="bold", y=0.98, color=C_DARK)

for fmt, ext in [("svg", ".svg"), ("pdf", ".pdf"), ("tiff", ".tiff")]:
    out_path = os.path.join(FIG_DIR, f"Fig5_temporal_trends{ext}")
    if fmt == "tiff":
        fig.savefig(out_path, dpi=600, format="tiff", pil_kwargs={"compression": "tiff_lzw"})
    else:
        fig.savefig(out_path, dpi=300, format=fmt, bbox_inches="tight")
    print(f"  Saved: {out_path}")

print("Figure 5 (temporal trends) done.")
