#!/usr/bin/env python3
"""
Figure 1 — Green Trade Trilemma conceptual framework (v13)
============================================================
Nature-editor review fixes:
  1. Unicode → ASCII: ≡→=, —→--, ±→+/-  (cross-platform font safety)
  2. Panel C y-axis labelpad 2→6 (fixes tick-label vs title crowding)
  3. Panel C reference note y 0.04→0.07 (avoids overlap with "0.6" tick)
  4. Panel B y-axis labelpad 3→5 (less crowded tick labels)
  5. "Trilemma zone" 6→6.5pt (legibility at print size)
  6. Panel C baseline line alpha 0.45→0.55, lw 0.6→0.8 (more visible)

Export: SVG (editable) + PDF + TIFF 600 dpi → figures_v13/
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Polygon
import numpy as np
import pandas as pd
import os

# ═══════════════════════════════════════════════
# Nature rcParams
# ═══════════════════════════════════════════════
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "figure.dpi": 72,          # SVG 1px = 1pt (Nature requirement)
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

# ═══════════════════════════════════════════════
# Unified colour palette
# ═══════════════════════════════════════════════
C_SPEED   = "#D45D2C"   # orange — deployment speed / GSI
C_DIVER   = "#2C6E8F"   # blue   — import diversity / GDI
C_EQUITY  = "#3A7D4A"   # green  — developing-country equity / GEI
C_ACCENT  = "#B64342"   # red    — policy / de-risking
C_DARK    = "#272727"   # near-black — main text, axes, data lines
C_NEUTRAL = "#767676"   # grey   — secondary elements, edges
C_LIGHT   = "#E8E0D8"   # warm grey — subtle fills (reserved)

TRI_COLORS = [C_SPEED, C_DIVER, C_EQUITY]

# Vertex labels: conceptual policy goals (capitalised consistently)
VERTEX_LABELS = [
    "Rapid\nDeployment",              # top — GSI goal
    "Import\nDiversity",              # bottom-left — GDI goal
    "Inclusive\nParticipation",       # bottom-right — GEI goal
]

# Arrow labels: descriptive adjectives (no acronyms — self-contained)
ARROW_LABELS = [
    "Faster,\ncheaper",
    "More\nresilient",
    "More\nequitable",
]

BASE = os.path.dirname(os.path.abspath(__file__))
FIG_DIR = os.path.join(BASE, "figures_v13")
os.makedirs(FIG_DIR, exist_ok=True)


def save_pub(fig, name, dpi=600):
    for ext in ["svg", "pdf", "tiff"]:
        kw = {"bbox_inches": "tight"}
        if ext == "tiff":
            kw["dpi"] = dpi
        fig.savefig(os.path.join(FIG_DIR, f"{name}.{ext}"), **kw)
    print(f"  -> {name}.svg / .pdf / .tiff")


def panel_label(ax, s, x=-0.06, y=1.06):
    ax.text(x, y, s, transform=ax.transAxes, fontsize=8,
            fontweight="bold", va="bottom", ha="left", color=C_DARK)


def data_path(fname):
    p = os.path.join(BASE, "data", "processed", fname)
    return p if os.path.exists(p) else None


# ═══════════════════════════════════════════════
# Bootstrap SE of median (cached)
# ═══════════════════════════════════════════════

def _bootstrap_se_median(vals, n_boot=500, seed=42):
    rng = np.random.RandomState(seed)
    n = len(vals)
    boot_meds = np.array([np.median(rng.choice(vals, size=n, replace=True))
                           for _ in range(n_boot)])
    se = np.std(boot_meds)
    floor = np.median(vals) * 0.002
    return max(se, floor)


# ═══════════════════════════════════════════════
# PANEL A — Trilemma Triangle
# ═══════════════════════════════════════════════

def draw_panel_a(ax):
    """Classical trilemma triangle.
    Vertices = conceptual policy goals (capitalised).
    Arrow labels = descriptive adjectives (informative without acronyms).
    Inner triangle = empty (white), dashed border, 'Trilemma zone' label."""
    r = 2.0
    ang = np.deg2rad([90, 210, 330])
    V = [(r * np.cos(a), r * np.sin(a)) for a in ang]

    ax.set_xlim(-2.6, 2.6)
    ax.set_ylim(-2.6, 2.8)
    ax.set_aspect("equal")
    ax.set_axis_off()

    # Triangle edges
    for i, j in [(0, 1), (1, 2), (2, 0)]:
        ax.plot([V[i][0], V[j][0]], [V[i][1], V[j][1]],
                color=C_NEUTRAL, lw=1.8, alpha=0.35, zorder=1)

    # Inner trilemma zone — white fill, dashed border
    scl = 0.35
    iv = [(x * scl, y * scl) for (x, y) in V]
    ax.add_patch(Polygon(iv, fc="white", ec=C_NEUTRAL, lw=0.8,
                         alpha=0.60, ls="--", zorder=2))
    ax.text(0, -0.08, "Trilemma\nzone", fontsize=6.5, color=C_NEUTRAL,
            ha="center", va="center", style="italic", alpha=0.8, zorder=3)

    # Vertex labels (outside triangle) — 8pt, bold
    offsets = [(0, 0.34), (-0.44, -0.28), (0.44, -0.28)]
    for (vx, vy), (ox, oy), lab, col in zip(V, offsets, VERTEX_LABELS, TRI_COLORS):
        ax.text(vx + ox, vy + oy, lab, fontsize=8, fontweight="bold",
                ha="center", va="center", color=col, zorder=20)

    # Outward arrows — descriptive labels at arrowhead, 6pt
    arrow_specs = [
        (0, ARROW_LABELS[0], C_SPEED),
        (1, ARROW_LABELS[1], C_DIVER),
        (2, ARROW_LABELS[2], C_EQUITY),
    ]
    for vi, label, col in arrow_specs:
        vx, vy = V[vi]
        tx, ty = vx * 0.28, vy * 0.28
        hx, hy = vx * 0.63, vy * 0.63
        lx, ly = vx * 0.78, vy * 0.78
        ax.annotate("", xy=(hx, hy), xytext=(tx, ty),
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.5,
                                    shrinkA=0, shrinkB=0),
                    zorder=21)
        ax.text(lx, ly, label, fontsize=6, color=col, fontweight="bold",
                ha="center", va="center", zorder=22)

    # Edge descriptions — 6pt, italic; vertex terminology (not old metric names)
    edge_specs = [
        ((V[0], V[2]), "Deployment vs.\nParticipation", ( 1.05,  0.18)),
        ((V[0], V[1]), "Deployment vs.\nDiversity",     (-1.05,  0.18)),
        ((V[1], V[2]), "Diversity vs.\nParticipation",  ( 0.00, -1.05)),
    ]
    for (vA, vB), txt, (ox, oy) in edge_specs:
        cx, cy = (vA[0] + vB[0]) / 2, (vA[1] + vB[1]) / 2
        ax.text(cx + ox, cy + oy, txt, fontsize=6, color=C_NEUTRAL,
                ha="center", va="center", style="italic", alpha=0.75, zorder=20)

    panel_label(ax, "a")


# ═══════════════════════════════════════════════
# PANEL B — GDI x GSI by income group (EQUAL-SPAN dual axes)
# ═══════════════════════════════════════════════

def draw_panel_b(ax):
    """Income-group divergence in GDI and GSI (2015-2024).
    DUAL y-axes with EQUAL 80-unit spans: GDI [25,105], GSI [35,115].
    Both spans equal -> visual proportions directly comparable.
    Legend note explains solid/dashed convention and uncertainty bands."""
    p = data_path("panel_analysis_ready.csv")
    if p is None:
        ax.text(0.5, 0.5, "Data unavailable", transform=ax.transAxes,
                ha="center", color=C_NEUTRAL)
        panel_label(ax, "b")
        return

    df = pd.read_csv(p)
    d = df[df["gdi"].notna() & df["gsi"].notna()]

    years_arr = np.sort(d["year"].unique())

    records = []
    for yr in years_arr:
        for is_dev in [True, False]:
            sub = d[(d["year"] == yr) & (d["is_developing"] == is_dev)]
            gdi_vals = sub["gdi"].dropna().values
            gsi_vals = sub["gsi"].dropna().values
            records.append({
                "year": yr,
                "is_developing": is_dev,
                "gdi_med": np.median(gdi_vals),
                "gsi_med": np.median(gsi_vals),
                "gdi_se": _bootstrap_se_median(gdi_vals),
                "gsi_se": _bootstrap_se_median(gsi_vals),
            })
    grp = pd.DataFrame(records)
    dev = grp[grp["is_developing"] == True]
    hinc = grp[grp["is_developing"] == False]

    d_gdi_2015 = dev["gdi_med"].values[0]
    d_gsi_2015 = dev["gsi_med"].values[0]
    h_gdi_2015 = hinc["gdi_med"].values[0]
    h_gsi_2015 = hinc["gsi_med"].values[0]

    dv = lambda c: dev[c].values
    hv = lambda c: hinc[c].values

    dev_gdi_pct  = dv("gdi_med") / d_gdi_2015 * 100
    dev_gdi_se   = dv("gdi_se")  / d_gdi_2015 * 100
    hi_gdi_pct   = hv("gdi_med") / h_gdi_2015 * 100
    hi_gdi_se    = hv("gdi_se")  / h_gdi_2015 * 100
    dev_gsi_pct  = dv("gsi_med") / d_gsi_2015 * 100
    dev_gsi_se   = dv("gsi_se")  / d_gsi_2015 * 100
    hi_gsi_pct   = hv("gsi_med") / h_gsi_2015 * 100
    hi_gsi_se    = hv("gsi_se")  / h_gsi_2015 * 100

    years = dv("year")

    print(f"  Panel b: GDI Dev {dev_gdi_pct[-1]:.0f}%  HI {hi_gdi_pct[-1]:.0f}% | "
          f"GSI Dev {dev_gsi_pct[-1]:.0f}%  HI {hi_gsi_pct[-1]:.0f}%")

    # ---- GDI (left axis, blue) — span 80: [25, 105] ----
    gdi_ylo, gdi_yhi = 25, 105

    ax.plot(years, dev_gdi_pct, color=C_DIVER, lw=1.8, marker="o", ms=4.4,
            mfc="white", mec=C_DIVER, mew=0.9, zorder=5)
    ax.fill_between(years, dev_gdi_pct - dev_gdi_se, dev_gdi_pct + dev_gdi_se,
                    color=C_DIVER, alpha=0.12, lw=0, zorder=2)

    ax.plot(years, hi_gdi_pct, color=C_DIVER, lw=1.5, ls="--", marker="s", ms=4.0,
            mfc="white", mec=C_DIVER, mew=0.8, zorder=4)
    ax.fill_between(years, hi_gdi_pct - hi_gdi_se, hi_gdi_pct + hi_gdi_se,
                    color=C_DIVER, alpha=0.12, lw=0, zorder=2)

    ax.set_ylabel("Import-source diversity (GDI)\nNormalised index (2015 = 100)",
                  fontsize=7, color=C_DIVER, labelpad=5)
    ax.tick_params(axis="y", labelsize=6, colors=C_DIVER)
    ax.set_ylim(gdi_ylo, gdi_yhi)

    # ---- GSI (right axis, orange) — span 80: [35, 115] ----
    ax2 = ax.twinx()
    gsi_ylo, gsi_yhi = 35, 115

    ax2.plot(years, dev_gsi_pct, color=C_SPEED, lw=1.8, marker="o", ms=4.4,
             mfc="white", mec=C_SPEED, mew=0.9, zorder=5)
    ax2.fill_between(years, dev_gsi_pct - dev_gsi_se, dev_gsi_pct + dev_gsi_se,
                     color=C_SPEED, alpha=0.12, lw=0, zorder=2)

    ax2.plot(years, hi_gsi_pct, color=C_SPEED, lw=1.5, ls="--", marker="s", ms=4.0,
             mfc="white", mec=C_SPEED, mew=0.8, zorder=4)
    ax2.fill_between(years, hi_gsi_pct - hi_gsi_se, hi_gsi_pct + hi_gsi_se,
                     color=C_SPEED, alpha=0.12, lw=0, zorder=2)

    ax2.set_ylabel("Deployment speed (GSI)\nNormalised index (2015 = 100)",
                    fontsize=7, color=C_SPEED, labelpad=5)
    ax2.tick_params(axis="y", labelsize=6, colors=C_SPEED)
    ax2.spines["right"].set_visible(True)
    ax2.spines["right"].set_color(C_SPEED)
    ax2.spines["right"].set_alpha(0.45)
    ax2.spines["right"].set_lw(0.5)
    ax2.set_ylim(gsi_ylo, gsi_yhi)

    # ---- x-axis ----
    ax.set_xlim(2014.5, 2025.5)
    ax.set_xlabel("Year", fontsize=7, labelpad=2)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(2))

    # ---- Direct line labels (disambiguated), 6pt ----
    # Use np.interp to get curve value AT the label's x-position,
    # then apply generous offset to avoid line/band overlap.
    dev_gdi_at_label = np.interp(2017.5, years, dev_gdi_pct)
    hi_gdi_at_label  = np.interp(2015.8, years, hi_gdi_pct)
    dev_gsi_at_label = np.interp(2019.1, years, dev_gsi_pct)
    hi_gsi_at_label  = np.interp(2019.1, years, hi_gsi_pct)

    ax.text(2017.5, dev_gdi_at_label - 10, "Dev (GDI)", fontsize=6,
            color=C_DIVER, fontweight="bold", ha="left", va="top")
    ax.text(2015.8, hi_gdi_at_label - 10, "HI (GDI)", fontsize=6,
            color=C_DIVER, fontweight="bold", ha="left", va="top")

    ax2.text(2019.1, dev_gsi_at_label - 10, "Dev (GSI)", fontsize=6,
             color=C_SPEED, fontweight="bold", ha="left", va="top")
    ax2.text(2019.1, hi_gsi_at_label + 10, "HI (GSI)", fontsize=6,
             color=C_SPEED, fontweight="bold", ha="left", va="bottom")

    # ---- % change labels at right edge, 6pt ----
    # Interpolated at label x-position, with clear offset from curve.
    # HI GSI uses smaller offset because its 2024 value (~46) is near ylim=35.
    pct_specs = [
        (ax,  dev_gdi_pct, C_DIVER,  -8),
        (ax,  hi_gdi_pct,  C_DIVER,  -8),
        (ax2, dev_gsi_pct, C_SPEED,  -10),
        (ax2, hi_gsi_pct,  C_SPEED,  -6),
    ]
    for arr, pct, col, dy in pct_specs:
        val_at_label = np.interp(2024.3, years, pct)
        arr.text(2024.3, val_at_label + dy,
                 f"{pct[-1]-100:+.0f}%", fontsize=6,
                 color=col, fontweight="bold", ha="left", va="center")

    # ---- Convention & uncertainty legend (bottom-left of GDI axis) ----
    legend_text = (
        "-- Solid: developing     -- Dashed: high-income\n"
        "Shading: +/- 1 bootstrap SE of median"
    )
    ax.text(2015.0, gdi_ylo + 15, legend_text, fontsize=6,
            color=C_NEUTRAL, ha="left", va="bottom", zorder=30)

    # ---- Annotations WITH arrows (matching panel c style), 6pt ----
    yr_idx = {y: list(years).index(y) for y in years}

    ax.annotate("GDI trajectories\ndiverging",
                xy=(2022, dev_gdi_pct[yr_idx[2022]]),
                xytext=(2023.0, dev_gdi_pct[yr_idx[2022]] + 4.5),
                fontsize=6, ha="center", color=C_DIVER, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=C_DIVER, lw=0.7,
                                shrinkA=2, shrinkB=2),
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none",
                          alpha=0.80),
                zorder=28)

    ax2.annotate("GSI declining for\nboth groups, faster\nfor high-income",
                 xy=(2021, hi_gsi_pct[yr_idx[2021]]),
                 xytext=(2021.5, hi_gsi_pct[yr_idx[2021]] + 25),
                 fontsize=6, ha="left", color=C_SPEED, fontweight="bold",
                 arrowprops=dict(arrowstyle="->", color=C_SPEED, lw=0.7,
                                 shrinkA=2, shrinkB=2),
                 bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none",
                           alpha=0.80),
                 zorder=28)

    panel_label(ax, "b")


# ═══════════════════════════════════════════════
# PANEL C — Trilemma decomposition (all medians)
# ═══════════════════════════════════════════════

def draw_panel_c(ax):
    """Global trilemma decomposition. ALL metrics use median.
    Legend in upper left. Neutral data-summary annotation with
    connector lines to 2024 endpoints."""
    p = data_path("panel_analysis_ready.csv")
    if p is None:
        ax.text(0.5, 0.5, "Data unavailable", transform=ax.transAxes,
                ha="center", color=C_NEUTRAL)
        panel_label(ax, "c")
        return

    df = pd.read_csv(p)

    yr = df.groupby("year").agg(
        gsi=("gsi", "median"),
        gdi=("gdi", "median"),
        gei=("gei", "median"),
        policy=("derisk_policy_index", "sum"),
    ).reset_index()

    years = yr["year"].values

    base = yr[yr["year"] == 2015].iloc[0]
    gsi_norm = yr["gsi"].values / base["gsi"]
    gdi_norm = yr["gdi"].values / base["gdi"]
    gei_norm = yr["gei"].values / base["gei"]
    pol = yr["policy"].values

    print(f"  Panel c: GSI={gsi_norm[-1]:.3f}  GDI={gdi_norm[-1]:.3f}  GEI={gei_norm[-1]:.3f}")

    ax.set_xlim(2014.3, 2024.7)
    ax.set_ylim(0.44, 1.44)
    ax.set_xlabel("Year", fontsize=7, labelpad=2)
    ax.set_ylabel("Normalised index (2015 = 1)", fontsize=7, labelpad=10)
    ax.axhline(1.0, color=C_NEUTRAL, lw=0.8, ls=":", alpha=0.55, zorder=1)

    # Policy background fill
    if pol.max() > 0:
        ax.fill_between(years, 0.45, 1.44,
                        where=(pol > 0),
                        color=C_ACCENT, alpha=0.14, zorder=1,
                        label="Policy response period")

    # Component trends
    ax.plot(years, gsi_norm, color=C_SPEED, lw=1.9, marker="o", ms=4.5,
            mfc="white", mec=C_SPEED, mew=1.1, zorder=6, label="GSI (deployment speed)")
    ax.plot(years, gdi_norm, color=C_DIVER, lw=1.9, marker="s", ms=4.5,
            mfc="white", mec=C_DIVER, mew=1.1, zorder=6, label="GDI (import diversity)")
    ax.plot(years, gei_norm, color=C_EQUITY, lw=1.9, marker="D", ms=4.5,
            mfc="white", mec=C_EQUITY, mew=1.1, zorder=6, label="GEI (equity)")

    yr_idx = {y: list(years).index(y) for y in years}

    gsi_delta = (gsi_norm[-1] - 1) * 100
    gdi_delta = (gdi_norm[-1] - 1) * 100
    gei_delta = (gei_norm[-1] - 1) * 100

    # 3 policy annotations — anchored to specific data lines, 6pt
    # Each: (year, y_data, dy, x_off, label, direction)
    # US annotations use opposing x_off to prevent bbox overlap (see v13 audit)
    annotations = [
        (2020, gdi_norm[yr_idx[2020]], -0.13, -0.8,
         "US Section 201\nextension +\nIndia PLI launch", "below"),
        (2022, gdi_norm[yr_idx[2022]], -0.13, +0.3,
         "US IRA + India BCD;\nEU CBAM negotiations\nbegin", "below"),
        (2024, gei_norm[yr_idx[2024]], +0.07, +0.05,
         "EU NZIA + Canada\n100% EV tariff\n+ UK CBAM", "above"),
    ]
    for yr_ev, y_data, dy, x_off, label, direction in annotations:
        if direction == "above":
            y_txt = y_data + abs(dy)
            va = "bottom"
        else:
            y_txt = y_data - abs(dy)
            va = "top"
        ax.annotate(label,
                    xy=(yr_ev, y_data),
                    xytext=(yr_ev + x_off, y_txt),
                    fontsize=6, ha="left", va=va,
                    color=C_ACCENT, fontweight="bold", zorder=25,
                    arrowprops=dict(arrowstyle="->", color=C_ACCENT, lw=0.7,
                                    shrinkA=2, shrinkB=2,
                                    connectionstyle="arc3,rad=0.08"))

    # ---- Right-edge % labels at endpoints (staggered, generous spacing) ----
    ax.text(2024.4, gsi_norm[-1] - 0.07,
            f"{gsi_delta:+.0f}%", fontsize=6,
            color=C_SPEED, fontweight="bold", ha="right", va="top")
    ax.text(2024.2, gdi_norm[-1] + 0.055,
            f"{gdi_delta:+.0f}%", fontsize=6,
            color=C_DIVER, fontweight="bold", ha="right", va="bottom")
    ax.text(2024.4, gei_norm[-1] - 0.045,
            f"{gei_delta:+.0f}%", fontsize=6,
            color=C_EQUITY, fontweight="bold", ha="right", va="top")

    # ---- Reference note at lower-left (contextualises endpoint % labels) ----
    ax.text(0.02, 0.015, "2015 -> 2024 change",
            fontsize=6, ha="left", va="bottom", color=C_NEUTRAL,
            style="italic", transform=ax.transAxes, zorder=27)

    # Legend — upper left (away from 2015 baseline data)
    ax.legend(fontsize=6, loc="upper left", handletextpad=0.5,
              borderpad=0.3, ncol=1)

    panel_label(ax, "c")


# ═══════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════

def main():
    print("=" * 54)
    print("Figure 1 — Green Trade Trilemma v13 (Nature-editor fixes)")
    print("=" * 54)

    fig = plt.figure(figsize=(7.2, 5.55))
    gs = fig.add_gridspec(2, 2, height_ratios=[2.2, 1.0],
                          hspace=0.32, wspace=0.55)

    ax_a = fig.add_subplot(gs[0, :])
    draw_panel_a(ax_a)

    ax_b = fig.add_subplot(gs[1, 0])
    draw_panel_b(ax_b)

    ax_c = fig.add_subplot(gs[1, 1])
    draw_panel_c(ax_c)

    fig.subplots_adjust(left=0.12, right=0.94, top=0.96, bottom=0.10,
                        hspace=0.38, wspace=0.55)

    save_pub(fig, "Fig1_trilemma_framework")
    plt.close(fig)
    print("Done.")


if __name__ == "__main__":
    main()
