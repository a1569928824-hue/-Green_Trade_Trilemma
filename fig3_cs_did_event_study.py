#!/usr/bin/env python3
"""
Figure 3 — Callaway-Sant'Anna (2021) doubly-robust event-study estimates.
Promoted from Extended Data to main figure. Nature-quality 3-panel layout.
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

C_COST = "#D45D2C"
C_GDI = "#2C6E8F"
C_GEI = "#3A7D4A"
C_DARK = "#272727"
C_NEUTRAL = "#767676"
C_FILL = "#F0F0F0"

BASE = os.path.dirname(os.path.abspath(__file__))
PROC = os.path.join(BASE, "data", "processed")
FIG_DIR = os.path.join(BASE, "figures_v13")
os.makedirs(FIG_DIR, exist_ok=True)

t_dyn = pd.read_csv(os.path.join(PROC, "cs_event_study_results.csv"))

outcomes = [
    ("Import cost (log)", "a  Import cost (log unit value)", C_COST,
     "Log points", "ns\n(ATT = +0.13, P = 0.14)"),
    ("GDI (Source Diversity)", "b  Import source diversity (GDI)", C_GDI,
     "GDI (0–1)", "ns\n(ATT = −0.002, P = 0.59)"),
    ("Dev-Country Import Share (GEI)", "c  Dev.-country import share (GEI)", C_GEI,
     "Share (0–1)", "ns\n(ATT = +0.004, P = 0.40)"),
]

fig, axes = plt.subplots(1, 3, figsize=(7.5, 3.0))
fig.subplots_adjust(left=0.08, right=0.96, top=0.88, bottom=0.17, wspace=0.35)

for ax, (outcome, title, color, ylabel, note) in zip(axes, outcomes):
    sub = t_dyn[t_dyn["outcome"] == outcome]
    if len(sub) == 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        continue

    et = sub["event_time"].values
    att = sub["att"].values
    se = sub["se"].values

    # Post-treatment shading
    ax.axvspan(-0.5, max(et) + 0.5, alpha=0.06, color="red", zorder=0)

    # Zero reference
    ax.axhline(0, color=C_DARK, linewidth=0.5, linestyle="--", zorder=1, alpha=0.5)

    # Treatment line
    ax.axvline(-0.5, color=C_NEUTRAL, linewidth=0.7, linestyle=":", zorder=1, alpha=0.6)

    # CI band
    ax.fill_between(et, att - 1.96 * se, att + 1.96 * se,
                    alpha=0.25, color=color, zorder=2)

    # Point estimates
    ax.plot(et, att, color=color, linewidth=1.5, marker="o", markersize=4.5,
            markerfacecolor="white", markeredgewidth=1.2, markeredgecolor=color, zorder=3)

    ax.set_xlabel("Years since policy implementation", fontsize=6.5)
    ax.set_ylabel(ylabel, fontsize=6.5)
    ax.set_title(title, loc="left", fontsize=7.5, fontweight="bold", color=C_DARK)
    ax.tick_params(labelsize=6)

    # Result annotation
    ax.text(0.03, 0.96, note, transform=ax.transAxes, fontsize=6,
            va="top", ha="left",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.85,
                      edgecolor=C_NEUTRAL, linewidth=0.5))

    # Set x-limits for cleaner look
    valid_et = et[sub["n_groups"] >= 2]  # only where we have at least 2 groups
    if len(valid_et) > 0:
        ax.set_xlim(min(valid_et) - 0.5, max(valid_et) + 0.5)

fig.suptitle("Callaway-Sant’Anna (2021) Doubly-Robust Event-Study Estimates",
             fontsize=8.5, fontweight="bold", y=0.98, color=C_DARK)
fig.text(0.5, 0.02, "Event-study estimates with 95% confidence intervals. "
         "Country and year fixed effects. Reference period: t = −1. "
         "All three outcomes not significant at α = 0.05.",
         ha="center", fontsize=5.5, fontstyle="italic", color=C_NEUTRAL)

for fmt, ext in [("svg", ".svg"), ("pdf", ".pdf"), ("tiff", ".tiff")]:
    out_path = os.path.join(FIG_DIR, f"Fig3_cs_did_event_study{ext}")
    if fmt == "tiff":
        fig.savefig(out_path, dpi=600, format="tiff", pil_kwargs={"compression": "tiff_lzw"})
    else:
        fig.savefig(out_path, dpi=300, format=fmt, bbox_inches="tight")
    print(f"  Saved: {out_path}")

print("Figure 3 (CS-DID event study) done.")
