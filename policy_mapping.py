#!/usr/bin/env python3
"""
Central policy-to-ISO3 country name mapping for all analysis scripts.
Fixes name mismatches between policy inventory and BACI trade data.
"""
import pandas as pd

# EU-27 member state ISO3 codes (all 27 are in the BACI panel)
EU27_ISO3 = [
    "AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN",
    "FRA", "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX",
    "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE",
]

# Policy country name -> ISO3 code manual mapping
# Panel uses World Bank country names; policy uses common/short names
POLICY_NAME_TO_ISO3 = {
    "USA": "USA",
    "South Korea": "KOR",
    # Taiwan (TWN) is NOT in BACI HS12 V202601 - excluded from analysis
    # EU is an aggregate entity - expanded to individual member states below
}

# Policy country name -> panel country name (for matching on "country" column)
POLICY_NAME_TO_PANEL_COUNTRY = {
    "USA": "United States",
    "South Korea": "Korea, Rep.",
}


def load_and_fix_policy(raw_dir):
    """
    Load policy inventory and fix country name mappings.
    Returns: (policy_df, first_policy_year_by_iso3)

    - Fixes USA -> United States, South Korea -> Korea, Rep.
    - Removes Taiwan (not in BACI)
    - Expands EU-level policies to all 27 EU member states
    """
    import os
    policy = pd.read_csv(os.path.join(raw_dir, "derisking_policy_inventory.csv"))

    # 1. Fix country names for direct matching to panel
    policy["country"] = policy["country"].replace(POLICY_NAME_TO_PANEL_COUNTRY)

    # 2. Remove Taiwan (TWN not in BACI HS12)
    policy = policy[policy["country"] != "Taiwan"].copy()

    # 3. Expand EU policies to individual EU member states
    # EU policies in the inventory:
    eu_policies = policy[policy["country"] == "EU"].copy()
    policy = policy[policy["country"] != "EU"].copy()

    # Map EU country ISO3 to panel country names
    # We need to find the panel country name for each EU ISO3
    # This is loaded from the panel in the calling script
    # For now, store EU policies with iso3 directly
    for _, eu_row in eu_policies.iterrows():
        for iso3 in EU27_ISO3:
            new_row = eu_row.to_dict()
            new_row["iso3"] = iso3
            new_row["country"] = None  # Will be resolved by the caller using iso3
            policy = pd.concat([policy, pd.DataFrame([new_row])], ignore_index=True)

    return policy


def build_policy_treatment_timing(policy, country_to_iso):
    """
    Build first treatment year per country.

    Args:
        policy: DataFrame with country names
        country_to_iso: dict mapping panel country name -> iso_code

    Returns:
        DataFrame with columns: iso_code, first_treat_year
    """
    # Map country names to ISO3
    # First try direct iso3 column (for expanded EU entries)
    if "iso3" in policy.columns:
        has_direct = policy["iso3"].notna()
        policy.loc[has_direct, "country"] = None

    # Use country_to_iso mapping for entries with country names
    policy["iso_code"] = policy["country"].map(country_to_iso)

    # For EU entries, use the iso3 column directly
    if "iso3" in policy.columns:
        eu_mask = policy["iso_code"].isna() & policy["iso3"].notna()
        policy.loc[eu_mask, "iso_code"] = policy.loc[eu_mask, "iso3"]

    policy = policy.dropna(subset=["iso_code"])

    # Get first treatment year per ISO code
    first_year = policy.groupby("iso_code")["year"].min().reset_index()
    first_year.columns = ["iso_code", "first_treat_year"]

    return first_year
