#!/usr/bin/env python3
"""数据真实性审计脚本"""
import pandas as pd
import os

RAW = r"F:\科研论文\投稿\Green_Trade_Trilemma_Proposal\data\raw"

# === 验证 1: IRENA 容量数据 ===
print("=" * 60)
print("验证 1: IRENA 容量数据 (OWID)")
print("=" * 60)
cap = pd.read_csv(os.path.join(RAW, "irena_capacity.csv"))
targets = ["China", "United States", "India", "Germany", "Japan"]
for t in targets:
    sub = cap[(cap["country"] == t) & (cap["year"] == 2024)]
    solar = sub[sub["technology"] == "Solar PV"]["capacity_mw"].sum()
    wind = sub[sub["technology"] == "Wind"]["capacity_mw"].sum()
    total = sub["capacity_mw"].sum()
    print(f"  {t:20s}: Solar={solar/1e6:.1f} TW, Wind={wind/1e6:.1f} TW, Total={total/1e6:.1f} TW")
print()
# IRENA 2025 报告: 中国太阳能 2024 ~887 GW, 风电 ~521 GW

# === 验证 2: World Bank WDI ===
print("=" * 60)
print("验证 2: World Bank WDI")
print("=" * 60)
wdi = pd.read_csv(os.path.join(RAW, "worldbank_wdi.csv"))
aggregates = wdi[wdi["country_code"].str.len() < 3]
print(f"  Aggregates in WDI: {len(aggregates)} rows, samples:")
for _, row in aggregates.head(5).iterrows():
    print(f"    {row['country_code']} = {row['country_name']}")
real = wdi[wdi["country_code"].str.len() == 3]
print(f"  Real countries (ISO3): {real.country_code.nunique()}")
chn = wdi[(wdi["country_code"] == "CHN") & (wdi["year"] == 2023)]
if len(chn) > 0:
    print(f"  China 2023 GDP/capita: ${chn.iloc[0]['gdp_per_capita_2015']:,.0f}")
print()

# === 验证 3: BACI 贸易数据 ===
print("=" * 60)
print("验证 3: BACI 贸易数据 (CEPII)")
print("=" * 60)
trade = pd.read_csv(os.path.join(RAW, "baci_low_carbon_trade.csv"))
total_by_year = trade.groupby("year")["value_kusd"].sum() / 1e9
print("  Annual trade value (USD billions):")
for y, v in total_by_year.items():
    print(f"    {y}: {v:.1f} B USD")
# 2023 主要产品
t2023 = trade[trade["year"] == 2023]
solar = t2023[t2023["hs6"].astype(str).str.startswith("85414")]
battery = t2023[t2023["hs6"] == 850760]
print(f"  2023 Solar (85414x): {solar['value_kusd'].sum()/1e9:.1f} B USD")
print(f"  2023 Battery (850760): {battery['value_kusd'].sum()/1e9:.1f} B USD")
print()

# 验证已知事实: 2023年全球太阳能电池出口中中国占主导
china_solar = solar[solar["exporter_iso"] == "CHN"]["value_kusd"].sum()
total_solar = solar["value_kusd"].sum()
print(f"  China share of solar exports: {china_solar/total_solar*100:.1f}%")

# 文件元数据
print()
print("=" * 60)
print("文件来源元数据")
print("=" * 60)
for fname in ["irena_capacity.csv", "worldbank_wdi.csv", "baci_low_carbon_trade.csv"]:
    fp = os.path.join(RAW, fname)
    size_mb = os.path.getsize(fp) / 1e6
    mtime = pd.Timestamp(os.path.getmtime(fp), unit="s")
    print(f"  {fname}: {size_mb:.1f} MB, modified {mtime}")
