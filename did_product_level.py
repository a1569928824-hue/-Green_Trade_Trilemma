#!/usr/bin/env python3
"""
Product-level DID with Bartik (Shift-Share) Instrument
======================================================
Exploits product-level variation in de-risking policy exposure.
Bartik instrument: pre-existing China import share x policy timing.
"""
import pandas as pd, numpy as np, os, io, zipfile, csv as csv_mod
from statsmodels.api import OLS
import warnings
warnings.filterwarnings("ignore")

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "raw")
PROC = os.path.join(BASE, "data", "processed")

print("=" * 70)
print("PRODUCT-LEVEL DID WITH BARTIK INSTRUMENT")
print("=" * 70)

# ===================================================================
# 1. LOAD AND PREPARE PRODUCT-LEVEL DATA
# ===================================================================
# Load BACI
baci = pd.read_csv(os.path.join(RAW, "baci_low_carbon_trade.csv"))
baci = baci[baci["year"] >= 2015].copy()

# Country codes
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

baci["importer_iso3"] = baci["importer_iso"].map(code_map)
baci["exporter_iso3"] = baci["exporter_iso"].map(code_map)

# ===================================================================
# 2. COMPUTE PRE-POLICY CHINA IMPORT SHARE PER PRODUCT-COUNTRY
# ===================================================================
print("\nComputing pre-policy China import shares (2015-2019)...")

pre_period = baci[baci["year"].between(2015, 2019)]

# Total imports per importer-product
total_imp = pre_period.groupby(["importer_iso3", "hs6"])["value_kusd"].sum().reset_index()
total_imp.columns = ["importer_iso3", "hs6", "total_import"]

# China imports per importer-product
chn_imp = pre_period[pre_period["exporter_iso3"] == "CHN"].groupby(
    ["importer_iso3", "hs6"])["value_kusd"].sum().reset_index()
chn_imp.columns = ["importer_iso3", "hs6", "china_import"]

# Merge and compute share
shares = total_imp.merge(chn_imp, on=["importer_iso3", "hs6"], how="left")
shares["china_import"] = shares["china_import"].fillna(0)
shares["china_share"] = shares["china_import"] / shares["total_import"].clip(lower=1)
shares["china_share"] = shares["china_share"].clip(0, 1)

print(f"  Pre-period product-country pairs: {len(shares):,}")
print(f"  Mean China share: {shares['china_share'].mean():.3f}")
print(f"  Products with China share > 50%: {(shares['china_share'] > 0.5).mean():.1%}")

# ===================================================================
# 3. BUILD PANEL: PRODUCT × IMPORTER × YEAR
# ===================================================================
print("\nBuilding product-importer-year panel...")

# Main analysis years
years = list(range(2015, 2025))
products = sorted(baci["hs6"].unique())

# Build annual bilateral flows at product level (keep quantity for unit values)
agg_cols = {"value_kusd": "sum", "quantity_tons": "sum"}
annual = baci.groupby(["year", "importer_iso3", "exporter_iso3", "hs6"]).agg(agg_cols).reset_index()

# Total imports
ann_total = annual.groupby(["year", "importer_iso3", "hs6"])[["value_kusd", "quantity_tons"]].sum().reset_index()
ann_total.columns = ["year", "importer_iso3", "hs6", "total_import", "total_quantity"]

# China imports
ann_chn = annual[annual["exporter_iso3"] == "CHN"].groupby(
    ["year", "importer_iso3", "hs6"])["value_kusd"].sum().reset_index()
ann_chn.columns = ["year", "importer_iso3", "hs6", "china_import"]

# Unit value = total value / total quantity (weighted)
ann_total["unit_value"] = ann_total["total_import"] / ann_total["total_quantity"].clip(lower=1)

# Merge
panel_p = ann_total.merge(ann_chn, on=["year", "importer_iso3", "hs6"], how="left")
panel_p["china_import"] = panel_p["china_import"].fillna(0)
panel_p["china_share"] = panel_p["china_import"] / panel_p["total_import"].clip(lower=1)

# Log outcomes
panel_p["log_total_import"] = np.log(panel_p["total_import"].clip(lower=1))
panel_p["log_unit_value"] = np.log(panel_p["unit_value"].clip(lower=0.01))

# Merge pre-period China share (time-invariant)
panel_p = panel_p.merge(
    shares[["importer_iso3", "hs6", "china_share"]].rename(columns={"china_share": "pre_china_share"}),
    on=["importer_iso3", "hs6"], how="left"
)
panel_p["pre_china_share"] = panel_p["pre_china_share"].fillna(0)

# ===================================================================
# 4. BUILD BARTIK INSTRUMENT
# ===================================================================
print("\nBuilding Bartik instrument...")

# Load policy data with fixed country name mapping
from policy_mapping import load_and_fix_policy, EU27_ISO3

policy = load_and_fix_policy(RAW)

# Use iso3 column (already set by load_and_fix_policy for EU entries)
# For non-EU entries, map country names to ISO3 using panel country_to_iso
policy["iso3_use"] = policy["iso3"]  # EU entries already have iso3
panel_iso_map = panel[["country", "iso_code"]].drop_duplicates().set_index("country")["iso_code"].to_dict()
# But panel uses csv, so we need a different approach
# Build a name-to-ISO3 from the policy data itself + known fixes
name_to_iso3_fix = {
    "United States": "USA", "India": "IND", "Turkey": "TUR", "Brazil": "BRA",
    "South Africa": "ZAF", "Japan": "JPN", "Korea, Rep.": "KOR",
    "Canada": "CAN", "Australia": "AUS", "Indonesia": "IDN",
    "United Kingdom": "GBR", "Viet Nam": "VNM", "Saudi Arabia": "SAU",
    "Mexico": "MEX", "Chile": "CHL", "Morocco": "MAR",
    "Russia": "RUS", "Malaysia": "MYS", "Thailand": "THA",
    "Philippines": "PHL", "Colombia": "COL", "Argentina": "ARG",
    "Nigeria": "NGA", "Egypt": "EGY", "Bangladesh": "BGD",
    "Pakistan": "PAK", "Norway": "NOR",
    "France": "FRA", "Germany": "DEU", "Italy": "ITA",
}
# Fill in missing iso3 from the name mapping
missing_mask = policy["iso3"].isna()
policy.loc[missing_mask, "iso3"] = policy.loc[missing_mask, "country"].map(name_to_iso3_fix)
policy = policy.dropna(subset=["iso3"])

# Get first policy year per country (ISO3)
first_policy = policy.groupby("iso3")["year"].min().reset_index()
first_policy.columns = ["importer_iso3", "first_policy_year"]

# Merge to panel
panel_p = panel_p.merge(first_policy, on="importer_iso3", how="left")
panel_p["first_policy_year"] = panel_p["first_policy_year"].fillna(9999)

# Post-policy indicator
panel_p["post"] = (panel_p["year"] >= panel_p["first_policy_year"]).astype(int)

# Policy intensity (cumulative per country-year)
policy_intensity = policy.groupby(["iso3", "year"])["derisk_intensity"].sum().reset_index()
policy_intensity.columns = ["importer_iso3", "year", "policy_intensity"]

panel_p = panel_p.merge(policy_intensity, on=["importer_iso3", "year"], how="left")
panel_p["policy_intensity"] = panel_p["policy_intensity"].fillna(0)

# Bartik instrument: pre-China-share × post-policy
panel_p["bartik"] = panel_p["pre_china_share"] * panel_p["post"]
panel_p["bartik_continuous"] = panel_p["pre_china_share"] * panel_p["policy_intensity"]

print(f"  Treated countries: {panel_p['post'].mean():.1%} of obs")
print(f"  Mean Bartik instrument: {panel_p['bartik'].mean():.4f}")

# ===================================================================
# 5. ESTIMATION
# ===================================================================
print("\n" + "=" * 70)
print("ESTIMATION RESULTS")
print("=" * 70)

# Filter to countries with some trade
panel_p = panel_p[panel_p["total_import"] > 0].copy()

for outcome, label in [
    ("log_unit_value", "Import unit value (log)"),
    ("log_total_import", "Import volume (log)"),
    ("china_share", "China import share"),
]:
    print(f"\n--- {label} ---")

    sub = panel_p.dropna(subset=[outcome, "pre_china_share"]).copy()
    if len(sub) < 1000:
        print("  Insufficient data")
        continue

    # OLS (naive)
    y = sub[outcome].values
    X = pd.concat([
        sub[["post", "pre_china_share"]],
        pd.get_dummies(sub["importer_iso3"], prefix="c", drop_first=True),
        pd.get_dummies(sub["year"], prefix="y", drop_first=True),
        pd.get_dummies(sub["hs6"], prefix="p", drop_first=True),
    ], axis=1).astype(float)

    m = OLS(y, X, missing="drop").fit()
    beta_post = m.params["post"]
    se_post = m.bse["post"]
    p_post = m.pvalues["post"]
    print(f"  OLS post: beta={beta_post:+.4f}, se={se_post:.4f}, p={p_post:.4f}")

    # IV: 2SLS first stage
    # First stage: regress policy_intensity on bartik
    endog = sub["policy_intensity"].values
    X_fs = pd.concat([
        sub[["bartik_continuous", "pre_china_share"]],
        pd.get_dummies(sub["importer_iso3"], prefix="c", drop_first=True),
        pd.get_dummies(sub["year"], prefix="y", drop_first=True),
        pd.get_dummies(sub["hs6"], prefix="p", drop_first=True),
    ], axis=1).astype(float)

    m_fs = OLS(endog, X_fs, missing="drop").fit()
    beta_fs = m_fs.params["bartik_continuous"]
    se_fs = m_fs.bse["bartik_continuous"]
    f_stat = (beta_fs / se_fs) ** 2 if se_fs > 0 else 0
    print(f"  First stage: beta={beta_fs:+.4f}, se={se_fs:.4f}, F={f_stat:.1f}")

    if f_stat > 10:
        # Second stage: fitted policy_intensity
        policy_hat = m_fs.fittedvalues
        X_ss = pd.concat([
            pd.DataFrame({"policy_hat": policy_hat.values}),
            sub[["pre_china_share"]].reset_index(drop=True),
            pd.get_dummies(sub["importer_iso3"], prefix="c", drop_first=True).reset_index(drop=True),
            pd.get_dummies(sub["year"], prefix="y", drop_first=True).reset_index(drop=True),
            pd.get_dummies(sub["hs6"], prefix="p", drop_first=True).reset_index(drop=True),
        ], axis=1).astype(float)

        m_ss = OLS(y, X_ss, missing="drop").fit()
        beta_iv = m_ss.params["policy_hat"]
        se_iv = m_ss.bse["policy_hat"]
        p_iv = m_ss.pvalues["policy_hat"]
        print(f"  IV (2SLS): beta={beta_iv:+.4f}, se={se_iv:.4f}, p={p_iv:.4f}")
    else:
        print(f"  IV: Weak instrument (F={f_stat:.0f} < 10), not reported")

    # Reduced form: Bartik directly on outcome
    X_rf = pd.concat([
        sub[["bartik_continuous", "pre_china_share"]],
        pd.get_dummies(sub["importer_iso3"], prefix="c", drop_first=True),
        pd.get_dummies(sub["year"], prefix="y", drop_first=True),
        pd.get_dummies(sub["hs6"], prefix="p", drop_first=True),
    ], axis=1).astype(float)
    m_rf = OLS(y, X_rf, missing="drop").fit()
    beta_rf = m_rf.params["bartik_continuous"]
    se_rf = m_rf.bse["bartik_continuous"]
    p_rf = m_rf.pvalues["bartik_continuous"]
    print(f"  Reduced form: beta={beta_rf:+.4f}, se={se_rf:.4f}, p={p_rf:.4f}")

# ===================================================================
# 6. HETEROGENEITY BY PRODUCT GROUP
# ===================================================================
print("\n" + "=" * 70)
print("HETEROGENEITY: By HS6 Product Category")
print("=" * 70)

# Product groups (based on our HS6 classification)
SOLAR_CODES = {"854140", "854142", "854143", "280461", "850440", "700719", "760611"}
WIND_CODES = {"850231", "841280", "848210", "848340", "850300", "730820"}
BATTERY_CODES = {"850760", "282520", "283691", "850650", "850720"}
SMART_GRID = {"902830", "853521", "853650", "853710", "903289"}

panel_p["product_group"] = "Other"
panel_p.loc[panel_p["hs6"].astype(str).isin(SOLAR_CODES), "product_group"] = "Solar PV"
panel_p.loc[panel_p["hs6"].astype(str).isin(WIND_CODES), "product_group"] = "Wind"
panel_p.loc[panel_p["hs6"].astype(str).isin(BATTERY_CODES), "product_group"] = "Battery"
panel_p.loc[panel_p["hs6"].astype(str).isin(SMART_GRID), "product_group"] = "Smart Grid"

for group in ["Solar PV", "Wind", "Battery", "Smart Grid", "Other"]:
    sub_g = panel_p[(panel_p["product_group"] == group) & (panel_p["total_import"] > 0)].dropna(subset=["log_unit_value"])
    if len(sub_g) < 500:
        continue

    y = sub_g["log_unit_value"].values
    X = pd.concat([
        sub_g[["policy_intensity"]],
        pd.get_dummies(sub_g["importer_iso3"], prefix="c", drop_first=True),
        pd.get_dummies(sub_g["year"], prefix="y", drop_first=True),
    ], axis=1).astype(float)

    try:
        m_g = OLS(y, X, missing="drop").fit()
        print(f"  {group:15s}: N={len(sub_g):,}, "
              f"beta={m_g.params['policy_intensity']:+.4f}({m_g.bse['policy_intensity']:.4f}), "
              f"p={m_g.pvalues['policy_intensity']:.4f}")
    except:
        print(f"  {group:15s}: estimation failed")

print("\nProduct-level DID analysis complete.")
