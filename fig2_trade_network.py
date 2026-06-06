#!/usr/bin/env python3
"""
Figure 2: Global Low-Carbon Technology Trade Network (2015 vs 2024)
Nature journal standard. Shows the star-shaped concentration around China.
"""
import pandas as pd, numpy as np, os, io, zipfile, csv as csv_mod
import matplotlib as mpl
import matplotlib.pyplot as plt
import networkx as nx

mpl.rcParams.update({
    "figure.dpi": 72,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial"],
    "font.size": 7.0,
    "axes.titlesize": 7.5,
    "axes.labelsize": 7.0,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "legend.fontsize": 6.0,
})

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "raw")
FIG_DIR = os.path.join(BASE, "figures_v13")
os.makedirs(FIG_DIR, exist_ok=True)

# ===================================================================
# Load trade data
# ===================================================================
print("Loading trade data...")
baci = pd.read_csv(os.path.join(RAW, "baci_low_carbon_trade.csv"))
baci = baci[baci["year"].isin([2015, 2024])].copy()

# Load country code mapping
with zipfile.ZipFile(os.path.join(RAW, "BACI_HS12_V202601.zip"), 'r') as zf:
    cc_file = [n for n in zf.namelist() if 'country_codes' in n.lower()][0]
    with zf.open(cc_file) as f:
        text = io.TextIOWrapper(f, encoding='utf-8', errors='replace')
        reader = csv_mod.reader(text)
        next(reader)
        code_map, name_map = {}, {}
        for row in reader:
            if len(row) >= 4 and row[3]:
                code_map[int(row[0])] = row[3]
                name_map[row[3]] = row[1]
        text.detach()

baci["exporter_iso3"] = baci["exporter_iso"].map(code_map)
baci["importer_iso3"] = baci["importer_iso"].map(code_map)
baci = baci.dropna(subset=["exporter_iso3", "importer_iso3"])

# Aggregate bilateral flows
flows = baci.groupby(["year", "exporter_iso3", "importer_iso3"])["value_kusd"].sum().reset_index()
flows["value_musd"] = flows["value_kusd"] / 1000  # to million USD

# Region mapping
REGIONS = {
    "CHN": "East Asia", "JPN": "East Asia", "KOR": "East Asia", "TWN": "East Asia",
    "HKG": "East Asia", "MNG": "East Asia", "MAC": "East Asia",
    "USA": "North America", "CAN": "North America", "MEX": "North America",
    "DEU": "Europe", "FRA": "Europe", "GBR": "Europe", "ITA": "Europe",
    "ESP": "Europe", "NLD": "Europe", "BEL": "Europe", "SWE": "Europe",
    "POL": "Europe", "AUT": "Europe", "CZE": "Europe", "DNK": "Europe",
    "FIN": "Europe", "GRC": "Europe", "IRL": "Europe", "PRT": "Europe",
    "ROU": "Europe", "SVK": "Europe", "SVN": "Europe", "BGR": "Europe",
    "HRV": "Europe", "EST": "Europe", "LVA": "Europe", "LTU": "Europe",
    "HUN": "Europe", "CHE": "Europe", "NOR": "Europe", "LUX": "Europe",
    "ISL": "Europe", "MLT": "Europe", "CYP": "Europe",
    "IND": "South Asia", "PAK": "South Asia", "BGD": "South Asia",
    "LKA": "South Asia", "NPL": "South Asia",
    "VNM": "SE Asia", "THA": "SE Asia", "MYS": "SE Asia", "IDN": "SE Asia",
    "PHL": "SE Asia", "SGP": "SE Asia", "KHM": "SE Asia", "MMR": "SE Asia",
    "LAO": "SE Asia", "BRN": "SE Asia",
    "BRA": "Latin America", "ARG": "Latin America", "CHL": "Latin America",
    "COL": "Latin America", "PER": "Latin America", "VEN": "Latin America",
    "ECU": "Latin America", "URY": "Latin America", "PRY": "Latin America",
    "BOL": "Latin America", "CRI": "Latin America", "PAN": "Latin America",
    "GTM": "Latin America", "DOM": "Latin America",
    "AUS": "Oceania", "NZL": "Oceania",
    "RUS": "Russia/CIS", "UKR": "Russia/CIS", "KAZ": "Russia/CIS",
    "BLR": "Russia/CIS", "UZB": "Russia/CIS",
    "TUR": "Middle East", "SAU": "Middle East", "ARE": "Middle East",
    "QAT": "Middle East", "KWT": "Middle East", "OMN": "Middle East",
    "BHR": "Middle East", "ISR": "Middle East", "IRN": "Middle East",
    "JOR": "Middle East", "LBN": "Middle East",
    "ZAF": "Sub-Saharan Africa", "NGA": "Sub-Saharan Africa",
    "KEN": "Sub-Saharan Africa", "ETH": "Sub-Saharan Africa",
    "GHA": "Sub-Saharan Africa", "TZA": "Sub-Saharan Africa",
    "UGA": "Sub-Saharan Africa", "CIV": "Sub-Saharan Africa",
    "SEN": "Sub-Saharan Africa", "MOZ": "Sub-Saharan Africa",
    "AGO": "Sub-Saharan Africa", "COD": "Sub-Saharan Africa",
    "ZMB": "Sub-Saharan Africa", "ZWE": "Sub-Saharan Africa",
    "BWA": "Sub-Saharan Africa", "NAM": "Sub-Saharan Africa",
    "MUS": "Sub-Saharan Africa", "MDG": "Sub-Saharan Africa",
    "CMR": "Sub-Saharan Africa", "MLI": "Sub-Saharan Africa",
    "BFA": "Sub-Saharan Africa", "NER": "Sub-Saharan Africa",
    "RWA": "Sub-Saharan Africa", "BDI": "Sub-Saharan Africa",
    "MWI": "Sub-Saharan Africa", "SWZ": "Sub-Saharan Africa",
}
REGION_COLORS = {
    "East Asia": "#E41A1C",
    "North America": "#377EB8",
    "Europe": "#4DAF4A",
    "South Asia": "#FF7F00",
    "SE Asia": "#F781BF",
    "Latin America": "#A65628",
    "Oceania": "#999999",
    "Russia/CIS": "#984EA3",
    "Middle East": "#FDC086",
    "Sub-Saharan Africa": "#BEAED4",
}

def get_region(iso3):
    return REGIONS.get(iso3, "Other")

def get_color(iso3):
    return REGION_COLORS.get(get_region(iso3), "#CCCCCC")

# ===================================================================
# Build network for each year
# ===================================================================
print("Building networks...")

# Geographic coordinates for deterministic layout (approximate centroids)
# Using Robinson-projection-like scaling: x = lon/180, y = lat/90
COUNTRY_COORDS = {
    "CHN": (104.0, 35.0), "JPN": (138.0, 36.0), "KOR": (127.5, 36.5), "TWN": (121.0, 24.0),
    "HKG": (114.2, 22.3), "MNG": (103.8, 46.8), "MAC": (113.5, 22.2),
    "USA": (-98.0, 39.0), "CAN": (-102.0, 60.0), "MEX": (-102.0, 23.0),
    "DEU": (10.5, 51.0), "FRA": (2.2, 46.6), "GBR": (-1.2, 53.0), "ITA": (12.5, 42.0),
    "ESP": (-3.7, 40.4), "NLD": (5.3, 52.1), "BEL": (4.5, 50.8), "SWE": (15.0, 62.0),
    "POL": (19.1, 52.2), "AUT": (14.3, 47.5), "CZE": (15.5, 49.8), "DNK": (10.0, 56.0),
    "FIN": (26.0, 64.0), "GRC": (22.0, 39.0), "IRL": (-8.0, 53.0), "PRT": (-8.2, 39.4),
    "ROU": (25.0, 46.0), "SVK": (19.5, 48.7), "SVN": (15.0, 46.1), "BGR": (25.5, 42.7),
    "HRV": (16.0, 45.2), "EST": (26.0, 59.0), "LVA": (25.0, 57.0), "LTU": (24.0, 55.5),
    "HUN": (19.5, 47.2), "CHE": (8.2, 46.8), "NOR": (8.5, 62.0), "LUX": (6.1, 49.8),
    "ISL": (-19.0, 65.0), "MLT": (14.5, 35.9), "CYP": (33.0, 35.0),
    "IND": (78.0, 21.0), "PAK": (70.0, 30.0), "BGD": (90.4, 23.7),
    "LKA": (80.8, 7.9), "NPL": (84.1, 28.4),
    "VNM": (106.0, 16.0), "THA": (100.5, 15.0), "MYS": (102.0, 4.2),
    "IDN": (113.9, -2.5), "PHL": (121.0, 13.0), "SGP": (103.8, 1.3),
    "KHM": (104.9, 12.5), "MMR": (96.0, 21.9), "LAO": (102.5, 18.0), "BRN": (114.9, 4.9),
    "BRA": (-53.0, -10.0), "ARG": (-64.0, -34.0), "CHL": (-70.6, -33.4),
    "COL": (-74.0, 4.6), "PER": (-76.0, -10.0), "VEN": (-66.6, 6.4),
    "ECU": (-78.5, -1.8), "URY": (-56.0, -33.0), "PRY": (-58.0, -23.0),
    "BOL": (-64.0, -17.0), "CRI": (-84.0, 9.9), "PAN": (-80.0, 9.0),
    "GTM": (-90.4, 15.8), "DOM": (-70.0, 19.0),
    "AUS": (133.8, -25.3), "NZL": (174.8, -41.3),
    "RUS": (90.0, 60.0), "UKR": (31.2, 49.0), "KAZ": (67.0, 48.0),
    "BLR": (28.0, 53.7), "UZB": (64.6, 41.4),
    "TUR": (35.2, 39.0), "SAU": (45.0, 24.0), "ARE": (54.0, 24.5),
    "QAT": (51.2, 25.3), "KWT": (47.6, 29.3), "OMN": (56.0, 21.0),
    "BHR": (50.5, 26.0), "ISR": (35.0, 31.5), "IRN": (53.0, 32.0),
    "JOR": (36.0, 31.0), "LBN": (35.9, 33.9),
    "ZAF": (23.0, -29.0), "NGA": (8.0, 9.0), "KEN": (37.0, -1.0),
    "ETH": (40.5, 9.0), "GHA": (-1.0, 8.0), "TZA": (35.0, -6.0),
    "UGA": (32.5, 1.3), "CIV": (-5.0, 8.0), "SEN": (-15.0, 14.5),
    "MOZ": (35.5, -18.0), "AGO": (17.5, -12.5), "COD": (23.7, -2.9),
    "ZMB": (28.0, -14.0), "ZWE": (30.0, -19.0), "BWA": (24.7, -22.3),
    "NAM": (18.5, -22.6), "MUS": (57.5, -20.3), "MDG": (46.9, -19.4),
    "CMR": (12.0, 6.0), "MLI": (-6.0, 17.0), "BFA": (-1.5, 12.3),
    "NER": (9.0, 18.0), "RWA": (30.0, -1.9), "BDI": (30.0, -3.4),
    "MWI": (34.0, -13.5), "SWZ": (31.5, -26.5),
}
def geo_to_xy(lon, lat, scale=0.018):
    """Convert geographic coordinates to plot coordinates, centering on China."""
    return ((lon - 104.0) * scale, (lat - 35.0) * scale * 1.1)

# Aggregate total trade value per country (for node size)
total_by_country = baci.groupby(["year", "exporter_iso3"])["value_kusd"].sum().reset_index()
total_by_country.columns = ["year", "iso3", "total_trade"]

fig, axes = plt.subplots(1, 2, figsize=(7.2, 4.0))
fig.subplots_adjust(left=0.02, right=0.98, top=0.95, bottom=0.05, wspace=0.01)

for panel_idx, year in enumerate([2015, 2024]):
    ax = axes[panel_idx]
    yr_flows = flows[flows["year"] == year].copy()

    # Filter: only include edges > $50M for clarity
    yr_flows = yr_flows[yr_flows["value_musd"] > 50]

    # Get node set
    nodes = set(yr_flows["exporter_iso3"]) | set(yr_flows["importer_iso3"])

    # Node sizes proportional to total trade
    yr_total = total_by_country[total_by_country["year"] == year]
    size_map = dict(zip(yr_total["iso3"], yr_total["total_trade"]))
    max_size = max(size_map.values()) if size_map else 1e6
    min_display = 50  # minimum node size

    G = nx.DiGraph()
    for _, row in yr_flows.iterrows():
        exp = row["exporter_iso3"]
        imp = row["importer_iso3"]
        if exp not in G:
            sz = max(min_display, np.sqrt(size_map.get(exp, max_size/1000) / max_size) * 600)
            G.add_node(exp, size=sz, region=get_region(exp), color=get_color(exp))
        if imp not in G:
            sz = max(min_display, np.sqrt(size_map.get(imp, max_size/1000) / max_size) * 600)
            G.add_node(imp, size=sz, region=get_region(imp), color=get_color(imp))
        G.add_edge(exp, imp, weight=row["value_musd"] / 50, opacity=min(1.0, row["value_musd"] / 5000))

    # Use deterministic geographic coordinates for node positions
    pos = {}
    for node in G.nodes():
        if node in COUNTRY_COORDS:
            lon, lat = COUNTRY_COORDS[node]
            pos[node] = np.array(geo_to_xy(lon, lat))
        else:
            pos[node] = np.array([0.0, 0.0])

    # Apply small jitter to reduce overlapping nodes in dense regions (Europe)
    rng = np.random.RandomState(42)
    for node in pos:
        if node != "CHN":
            jitter_scale = 0.06 if get_region(node) == "Europe" else 0.04
            pos[node] += rng.normal(0, jitter_scale, 2)

    # Draw edges (only if both endpoints have positions)
    edge_weights = []
    for u, v, d in G.edges(data=True):
        if u in pos and v in pos:
            edge_weights.append(d.get("opacity", 0.3))

    # Batch draw edges
    for u, v, d in G.edges(data=True):
        if u in pos and v in pos:
            alpha = min(0.6, d.get("opacity", 0.1))
            width = d.get("weight", 0.5) * 0.5
            ax.plot(
                [pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
                color="gray", alpha=alpha, linewidth=width, zorder=1,
            )

    # Draw nodes
    for node, data in G.nodes(data=True):
        if node in pos:
            color = data.get("color", "#CCCCCC")
            size = data.get("size", 100)
            ax.scatter(pos[node][0], pos[node][1], s=size, c=color,
                      edgecolors="white", linewidth=0.5, zorder=2, alpha=0.9)

    # Label China
    if "CHN" in pos:
        ax.annotate("China", xy=pos["CHN"], fontsize=8, fontweight="bold",
                   ha="center", va="center", color="white",
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="#E41A1C", alpha=0.9,
                            edgecolor="none"))

    # Label a few other major nodes
    major = ["USA", "DEU", "JPN", "KOR", "IND"]
    for iso in major:
        if iso in pos and iso != "CHN":
            name = name_map.get(iso, iso)
            ax.annotate(name, xy=pos[iso], fontsize=6, ha="center", va="bottom",
                       xytext=(0, -6), textcoords="offset points", fontweight="bold")

    ax.set_xlim(-4.0, 1.0)
    ax.set_ylim(-2.0, 1.2)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"{'a' if year==2015 else 'b'}  {year}", loc="left", fontsize=8, fontweight="bold",
                pad=2)

# Legend
legend_elements = []
for region, color in REGION_COLORS.items():
    legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color,
                                      markersize=8, label=region, markeredgecolor='white', markeredgewidth=0.5))
fig.legend(handles=legend_elements, loc='lower center', ncol=5, fontsize=5.5,
          frameon=False, bbox_to_anchor=(0.5, -0.02))

# Global title
fig.suptitle("Global Low-Carbon Technology Trade Network", fontsize=9, fontweight="bold", y=0.98)

# Save
for fmt, ext in [("svg", ".svg"), ("pdf", ".pdf"), ("tiff", ".tiff")]:
    out_path = os.path.join(FIG_DIR, f"Fig2_trade_network{ext}")
    if fmt == "tiff":
        fig.savefig(out_path, dpi=600, format="tiff", pil_kwargs={"compression": "tiff_lzw"})
    else:
        fig.savefig(out_path, dpi=300, format=fmt, bbox_inches="tight")
    print(f"  Saved: {out_path}")

print("Figure 2 done.")
