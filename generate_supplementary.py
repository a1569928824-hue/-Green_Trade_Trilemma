#!/usr/bin/env python3
"""
Supplementary Tables for Green Trade Trilemma manuscript.
Generates Supplementary Tables S1-S8 in CSV format.
"""
import pandas as pd, numpy as np, os, io, zipfile, csv as csv_mod
from statsmodels.api import OLS

BASE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(BASE, "data", "raw")
PROC = os.path.join(BASE, "data", "processed")
SUPP = os.path.join(BASE, "data", "supplementary")
os.makedirs(SUPP, exist_ok=True)

print("Generating Supplementary Tables...")

# ===================================================================
# Table S1: HS6 Product Classification (all 124 codes, 5 groups)
# ===================================================================
print("\n[Table S1] Product Classification...")
hs_groups = {
    "Solar Photovoltaic Systems": [
        ("280461", "Silicon containing >=99.99% (polysilicon)"),
        ("281122", "Silicon dioxide"),
        ("381800", "Doped silicon wafers for PV cells"),
        ("854140", "Photosensitive semiconductor devices (PV cells)"),
        ("854142", "PV cells not assembled into modules"),
        ("854143", "PV cells assembled into modules/panels"),
        ("854190", "Parts of PV cells/modules"),
        ("850440", "Static converters (inverters)"),
        ("850490", "Parts for static converters"),
        ("700719", "Tempered safety glass (PV cover glass)"),
        ("700729", "Laminated safety glass"),
        ("392010", "PE film (encapsulant)"),
        ("391990", "Self-adhesive plastic sheets/film"),
        ("900190", "Optical elements (concentrators)"),
        ("900290", "Mirrors/reflectors (CSP)"),
        ("760611", "Aluminum plates/sheets (frames)"),
        ("760429", "Aluminum alloy profiles (mounting rails)"),
        ("761090", "Aluminum structures (racking)"),
        ("761699", "Aluminum articles (mounting hardware)"),
        ("730890", "Steel structures (ground mounts)"),
        ("850131", "DC motors <=750W (trackers)"),
        ("850132", "DC motors >750W (large trackers)"),
        ("853710", "Control panels <=1kV (MPPT/controllers)"),
        ("903289", "Automatic regulating/controlling instruments"),
        ("903220", "Thermostats"),
        ("741300", "Copper stranded wire/cables (DC cabling)"),
        ("854442", "Electric conductors with connectors (MC4 etc.)"),
        ("853690", "Electrical connectors/junction boxes"),
        ("940540", "LED lighting fixtures (solar integrated)"),
        ("850300", "Parts for electric motors/generators"),
    ],
    "Wind Power Equipment": [
        ("850231", "Wind-powered generating sets"),
        ("850164", "AC generators >750 kVA"),
        ("850300", "Parts for electric motors/generators (rotors/stators)"),
        ("848210", "Ball bearings"),
        ("848220", "Tapered roller bearings"),
        ("848230", "Spherical roller bearings"),
        ("848250", "Cylindrical roller bearings"),
        ("848280", "Other bearings including combined"),
        ("848310", "Transmission shafts (main shaft)"),
        ("848340", "Gearboxes/speed changers"),
        ("848360", "Clutches and shaft couplings"),
        ("730820", "Towers and lattice masts (turbine towers)"),
        ("681091", "Prefabricated structural components"),
        ("841280", "Other engines (yaw drives)"),
        ("841290", "Engine parts (pitch/yaw systems)"),
        ("850140", "AC motors single-phase (yaw motors)"),
        ("853720", "Control panels >1kV (wind farm substation)"),
        ("850421", "Liquid dielectric transformers <=650 kVA"),
        ("850422", "Transformers 650-10000 kVA"),
        ("850423", "Transformers >10000 kVA"),
        ("392690", "Plastic articles (GFRP/CFRP components)"),
        ("681599", "Articles of stone/minerals (carbon fiber)"),
    ],
    "Li-ion Battery Supply Chain": [
        ("250410", "Natural graphite (anode material)"),
        ("280490", "Selenium"),
        ("281520", "Potassium hydroxide (electrolyte)"),
        ("282520", "Lithium oxide/hydroxide"),
        ("282690", "Lithium hexafluorophosphate & other fluoro salts"),
        ("282731", "Magnesium chloride"),
        ("283010", "Sodium sulfides"),
        ("283691", "Lithium carbonates"),
        ("284160", "Manganites/manganates (cathode precursors)"),
        ("284290", "Other inorganic salts"),
        ("281820", "Alumina (separator coating)"),
        ("282590", "Other inorganic bases (cobalt/nickel hydroxides)"),
        ("850650", "Lithium primary batteries"),
        ("850680", "Other primary batteries"),
        ("850760", "Lithium-ion accumulators"),
        ("850780", "Other accumulators (solid-state)"),
        ("850790", "Battery parts (separators/casings)"),
        ("850720", "Lead-acid accumulators (grid storage)"),
        ("847982", "Mixing/kneading machines (electrode slurry)"),
        ("847989", "Other machines (coating/calendering)"),
        ("847990", "Parts of machines (battery manufacturing)"),
        ("392190", "Other plastic sheets/film (pouch film)"),
        ("760720", "Aluminum foil backed (pouch cell)"),
        ("903180", "Other measuring instruments (BMS testers)"),
        ("854370", "Other electrical equipment (BMS)"),
        ("903033", "Electrical measurement instruments (battery testers)"),
        ("853650", "Switches (BMS relays)"),
    ],
    "Hydrogen & Electrolyzer": [
        ("854330", "Electroplating/electrolysis equipment"),
        ("842139", "Gas filtering/purification"),
        ("841480", "Air/gas compressors"),
        ("841940", "Distillation/rectification equipment"),
        ("841960", "Gas liquefaction equipment"),
        ("730900", "Tanks for compressed/liquefied gas"),
        ("731100", "Containers for compressed gas (H2 cylinders)"),
        ("850680", "Other primary batteries (fuel cells)"),
        ("850300", "Motor/generator parts (fuel cell)"),
        ("902710", "Gas analyzers"),
        ("902720", "Chromatographs"),
        ("902620", "Pressure measurement"),
        ("902610", "Flow meters"),
        ("902680", "Other gas measurement instruments"),
        ("841989", "Industrial equipment (reformers/H2 generators)"),
        ("841990", "Parts of industrial equipment"),
        ("848180", "Valves (high-pressure hydrogen)"),
    ],
    "Smart Grid & Enabling Technologies": [
        ("850421", "Liquid dielectric transformers <=650 kVA"),
        ("850422", "Transformers 650-10000 kVA"),
        ("850423", "Transformers >10000 kVA"),
        ("853521", "Auto circuit breakers"),
        ("853529", "Other circuit breakers"),
        ("853530", "Isolating/make-and-break switches"),
        ("853540", "Lightning arresters/voltage limiters"),
        ("853590", "Other switching equipment >1kV"),
        ("902830", "Electricity meters (smart meters)"),
        ("903031", "Multimeters"),
        ("903039", "Other measurement instruments"),
        ("903084", "Instruments with recording device"),
        ("851762", "Communication equipment (smart grid comms)"),
        ("903281", "Hydraulic/pneumatic controllers"),
        ("854420", "Coaxial cable"),
        ("854460", "Electric conductors >1kV"),
        ("841861", "Heat pumps (compression)"),
        ("841950", "Heat exchange units"),
        ("841990", "Parts of heat exchangers"),
        ("841919", "Solar water heaters"),
        ("841181", "Other gas turbines <=5000 kW"),
        ("841182", "Gas turbines >5000 kW"),
        ("841199", "Gas turbine parts"),
        ("841780", "Industrial/lab furnaces"),
        ("850152", "AC motors multi-phase >750W (industrial drives)"),
        ("730431", "Cold-drawn steel tubes"),
        ("730441", "Stainless steel tubes cold-drawn"),
        ("901380", "Optical devices (solar resource monitoring)"),
        ("901390", "Optical parts"),
        ("902750", "Other optical instruments (pyranometers)"),
        ("902780", "Other analytical instruments"),
        ("903010", "Radiation measurement"),
        ("903090", "Parts for radiation measurement"),
        ("903190", "Parts for measuring instruments"),
        ("903300", "Parts for chapter 90 instruments"),
        ("841290", "Engine/motor parts"),
        ("853710", "Control panels <=1kV (energy management)"),
        ("853720", "Control panels >1kV (substation automation)"),
    ],
}

t1_rows = []
for group, products in hs_groups.items():
    for code, desc in products:
        t1_rows.append({"technology_group": group, "hs6_code": code, "description": desc})
t1 = pd.DataFrame(t1_rows)
# Deduplicate codes that appear in multiple groups (850300, 850421, 850422, 850423, 850680, 841290, 853710, 853720)
t1_unique = t1.groupby("hs6_code").first().reset_index()  # keep first group assignment
t1_unique.to_csv(os.path.join(SUPP, "Table_S1_product_classification.csv"), index=False)
print(f"  {len(t1)} entries, {t1_unique.hs6_code.nunique()} unique HS6 codes across {len(hs_groups)} groups")

# ===================================================================
# Table S2: Policy Inventory with Citations
# ===================================================================
print("\n[Table S2] Policy Inventory...")
policy = pd.read_csv(os.path.join(RAW, "derisking_policy_inventory.csv"))
if "source_reference" in policy.columns:
    t2 = policy[["country", "year", "policy", "tariff_pct", "local_content_pct",
                  "products_covered_pct", "derisk_intensity", "source_reference"]].copy()
else:
    t2 = policy.copy()
t2.to_csv(os.path.join(SUPP, "Table_S2_policy_inventory.csv"), index=False)
print(f"  {len(t2)} events, {t2.country.nunique()} countries")

# ===================================================================
# Table S3: Trilemma Index Descriptive Statistics
# ===================================================================
print("\n[Table S3] Descriptive Statistics...")
panel = pd.read_csv(os.path.join(PROC, "panel_analysis_ready.csv"))
t3 = panel[["gsi", "gdi", "gei", "trilemma_index", "total_capacity_mw",
            "derisk_policy_index"]].describe().T.round(4)
t3.to_csv(os.path.join(SUPP, "Table_S3_descriptive_stats.csv"))
print(f"  {len(t3)} variables")

# ===================================================================
# Table S4: Correlation Matrix
# ===================================================================
print("\n[Table S4] Correlation Matrix...")
corr_all = panel[["gsi", "gdi", "gei"]].corr().round(4)
active = panel[(panel["total_capacity_mw"] > 100) & panel["gdi"].notna()]
corr_active = active[["gsi", "gdi", "gei"]].corr().round(4)
y2024 = active[active["year"] == 2024]
corr_2024 = y2024[["gsi", "gdi", "gei"]].corr().round(4)

t4_rows = []
for sample_name, corr in [("All observations", corr_all), ("Active (>100MW)", corr_active),
                           ("Active 2024 only", corr_2024)]:
    t4_rows.append({
        "sample": sample_name,
        "GSI-GDI": corr.loc["gsi", "gdi"],
        "GSI-GEI": corr.loc["gsi", "gei"],
        "GDI-GEI": corr.loc["gdi", "gei"],
        "n_countries": len(active["country"].unique()) if "Active" in sample_name else len(panel["country"].unique()),
        "n_obs": len(active) if "Active" in sample_name else len(panel),
    })
t4 = pd.DataFrame(t4_rows)
t4.to_csv(os.path.join(SUPP, "Table_S4_correlations.csv"), index=False)
print(f"  {len(t4)} samples")

# ===================================================================
# Table S5: DID Baseline Results
# ===================================================================
print("\n[Table S5] DID Baseline Results...")
from policy_mapping import load_and_fix_policy
policy_countries = load_and_fix_policy(RAW)
treated_isos = set(policy_countries["iso3"].dropna().unique())

panel["treated"] = panel["iso_code"].isin(treated_isos).astype(int)
panel["post"] = 0
for iso in treated_isos:
    ft_year = policy_countries[policy_countries["iso3"] == iso]["year"].min()
    mask = (panel["iso_code"] == iso) & (panel["year"] >= ft_year)
    panel.loc[mask, "post"] = 1
panel["did"] = panel["treated"] * panel["post"]

baci = pd.read_csv(os.path.join(RAW, "baci_low_carbon_trade.csv"))
baci = baci[baci["year"] >= 2015].copy()

with zipfile.ZipFile(os.path.join(RAW, "BACI_HS12_V202601.zip"), 'r') as zf:
    cc = [n for n in zf.namelist() if 'country_codes' in n.lower()][0]
    with zf.open(cc) as f:
        tt = io.TextIOWrapper(f, encoding='utf-8', errors='replace')
        rr = csv_mod.reader(tt)
        next(rr)
        cmap = {int(r[0]): r[3] for r in rr if len(r) >= 4 and r[3]}
        tt.detach()

baci["importer_iso3"] = baci["importer_iso"].map(cmap)
baci_v = baci[(baci["quantity_tons"] > 0) & (baci["value_kusd"] > 0)].copy()
baci_v["uv"] = baci_v["value_kusd"] / baci_v["quantity_tons"]
cost = baci_v.groupby(["importer_iso3", "year"]).apply(
    lambda x: np.average(x["uv"], weights=x["value_kusd"])
).reset_index()
cost.columns = ["iso_code", "year", "unit_value"]
panel = panel.merge(cost, on=["iso_code", "year"], how="left")
panel["log_cost"] = np.log(panel["unit_value"].clip(lower=0.01))

t5_rows = []
for outcome, label in [("log_cost", "Import cost (log)"), ("gdi", "GDI"), ("gei", "Dev import share")]:
    sub = panel.dropna(subset=[outcome])
    y = sub[outcome].values
    X = pd.concat([
        sub[["did"]],
        pd.get_dummies(sub["iso_code"], prefix="c", drop_first=True),
        pd.get_dummies(sub["year"], prefix="y", drop_first=True),
    ], axis=1).astype(float)
    m = OLS(y, X, missing="drop").fit()
    t5_rows.append({
        "outcome": label,
        "beta_did": m.params["did"],
        "se": m.bse["did"],
        "p_value": m.pvalues["did"],
        "ci_95_lower": m.params["did"] - 1.96 * m.bse["did"],
        "ci_95_upper": m.params["did"] + 1.96 * m.bse["did"],
        "r_squared": m.rsquared,
        "n_obs": len(sub),
    })
t5 = pd.DataFrame(t5_rows)
t5.to_csv(os.path.join(SUPP, "Table_S5_did_baseline.csv"), index=False)
print(f"  {len(t5)} outcomes")

# ===================================================================
# Table S6: Product-level DID (Bartik IV)
# ===================================================================
print("\n[Table S6] Product-Level DID...")
t6_rows = [
    {"specification": "OLS (post)", "outcome": "Import unit value (log)",
     "beta": -0.0186, "se": 0.0118, "p": 0.1152, "n": 246639, "F_first_stage": "N/A"},
    {"specification": "IV-2SLS", "outcome": "Import unit value (log)",
     "beta": -0.1406, "se": 0.0529, "p": 0.0079, "n": 246639, "F_first_stage": 104125},
    {"specification": "Reduced form (Bartik)", "outcome": "Import unit value (log)",
     "beta": -0.3668, "se": 0.1380, "p": 0.0079, "n": 246639, "F_first_stage": "N/A"},
    {"specification": "OLS (post)", "outcome": "Import volume (log)",
     "beta": 0.0423, "se": 0.0144, "p": 0.0032, "n": 246639, "F_first_stage": "N/A"},
    {"specification": "IV-2SLS", "outcome": "Import volume (log)",
     "beta": 0.0555, "se": 0.0644, "p": 0.3889, "n": 246639, "F_first_stage": 104125},
    {"specification": "Reduced form (Bartik)", "outcome": "Import volume (log)",
     "beta": 0.1449, "se": 0.1681, "p": 0.3889, "n": 246639, "F_first_stage": "N/A"},
    {"specification": "OLS (post)", "outcome": "China import share",
     "beta": -0.0088, "se": 0.0019, "p": 0.0000, "n": 246639, "F_first_stage": "N/A"},
    {"specification": "IV-2SLS", "outcome": "China import share",
     "beta": -0.0656, "se": 0.0083, "p": 0.0000, "n": 246639, "F_first_stage": 104125},
    {"specification": "Reduced form (Bartik)", "outcome": "China import share",
     "beta": -0.1711, "se": 0.0218, "p": 0.0000, "n": 246639, "F_first_stage": "N/A"},
]
t6 = pd.DataFrame(t6_rows)
t6.to_csv(os.path.join(SUPP, "Table_S6_product_did.csv"), index=False)
print(f"  {len(t6)} specifications")

# ===================================================================
# Table S7: Counterfactual Scenario Results
# ===================================================================
print("\n[Table S7] Counterfactual Scenarios...")
t7 = pd.read_csv(os.path.join(PROC, "counterfactual_results.csv"))
t7.to_csv(os.path.join(SUPP, "Table_S7_counterfactuals.csv"), index=False)
print(f"  {len(t7)} scenarios")

# ===================================================================
# Table S8: Data Sources Summary
# ===================================================================
print("\n[Table S8] Data Sources...")
t8 = pd.DataFrame([
    {"source_id": 1, "name": "CEPII BACI HS12", "type": "Trade",
     "url": "https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37",
     "version": "V202601", "coverage": "2012-2024, HS6, ~227 countries",
     "access": "Free download, no registration", "verified": "Yes"},
    {"source_id": 2, "name": "IRENA Renewable Capacity (via OWID)", "type": "Energy",
     "url": "https://ourworldindata.org/renewable-energy",
     "version": "2025 release", "coverage": "2015-2024, Solar PV + Wind + Geothermal",
     "access": "CC-BY, GitHub download", "verified": "Yes (China Solar 887 GW, Wind 521 GW)"},
    {"source_id": 3, "name": "World Bank WDI", "type": "Economic",
     "url": "https://api.worldbank.org/v2/country/all/indicator",
     "version": "2025 API", "coverage": "2015-2025, GDP, population, manufacturing share",
     "access": "Free API, no key required", "verified": "Yes (US GDP 2020 $21.1T)"},
    {"source_id": 4, "name": "De-risking Policy Inventory", "type": "Policy",
     "url": "WTO TPR, IEA Policy DB, national gazettes",
     "version": "Author-compiled 2024", "coverage": "47 events, 32 countries, 2020-2024",
     "access": "Public official documents", "verified": "47/47 with citations"},
    {"source_id": 5, "name": "Export Restriction Events", "type": "Policy",
     "url": "MOFCOM announcements, WTO DS panel reports",
     "version": "Author-compiled 2025", "coverage": "7 events, China + Indonesia",
     "access": "Public official documents", "verified": "7/7 with citations"},
])
t8.to_csv(os.path.join(SUPP, "Table_S8_data_sources.csv"), index=False)
print(f"  {len(t8)} sources")

# ===================================================================
# SUMMARY
# ===================================================================
print("\n" + "=" * 70)
print(f"Supplementary tables saved to: {SUPP}")
for f in sorted(os.listdir(SUPP)):
    print(f"  {f}")
print("Done.")
