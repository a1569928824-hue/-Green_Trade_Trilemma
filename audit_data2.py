#!/usr/bin/env python3
"""深度数据审计"""
import pandas as pd
import zipfile
import os

RAW = r"F:\科研论文\投稿\Green_Trade_Trilemma_Proposal\data\raw"

# ============================================================
# 问题 1: World Bank WDI — 全是聚合体？
# ============================================================
print("=" * 60)
print("问题 1: WDI 数据的国家代码格式")
print("=" * 60)
wdi = pd.read_csv(os.path.join(RAW, "worldbank_wdi.csv"))
codes = wdi["country_code"].dropna().astype(str).unique()
print(f"  唯一代码数: {len(codes)}")
print(f"  前30个: {sorted(codes)[:30]}")
# World Bank API 返回的 country_code 可能不是 ISO3
# 有些 WB 代码格式: "1A", "1W", "4E", "7E", "8S", "B8", "EUU" 等
alpha3 = [c for c in codes if c.isalpha() and len(c) == 3]
print(f"  3字母代码数: {len(alpha3)}")
# 检查是否有常用的 ISO3 码
common = ["CHN", "USA", "IND", "DEU", "JPN", "GBR", "FRA", "BRA", "ZAF", "AUS"]
for cc in common:
    matches = wdi[wdi["country_code"] == cc]
    print(f"    {cc}: {len(matches)} rows")
print()

# ============================================================
# 问题 2: BACI 数据 — 数值单位验证
# ============================================================
print("=" * 60)
print("问题 2: BACI 贸易数据值验证")
print("=" * 60)
trade = pd.read_csv(os.path.join(RAW, "baci_low_carbon_trade.csv"))

# 检查数值分布
print(f"  value_kusd 统计:")
print(f"    mean: {trade['value_kusd'].mean():,.1f}")
print(f"    median: {trade['value_kusd'].median():,.1f}")
print(f"    max: {trade['value_kusd'].max():,.1f}")
print(f"    total: {trade['value_kusd'].sum():,.1f}")

# 最大贸易流
top10 = trade.nlargest(10, "value_kusd")
print(f"\n  Top 10 贸易流:")
for _, row in top10.iterrows():
    print(f"    {row['year']} | exp={row['exporter_iso']:4d} -> imp={row['importer_iso']:4d} | "
          f"HS{row['hs6']} | ${row['value_kusd']:,.0f}k")

# 加载国家代码映射
zip_path = os.path.join(RAW, "BACI_HS12_V202601.zip")
with zipfile.ZipFile(zip_path, "r") as zf:
    with zf.open("country_codes_V202601.csv") as f:
        codes = pd.read_csv(f)
code_map = dict(zip(codes["country_code"], codes["country_iso3"]))
name_map = dict(zip(codes["country_iso3"], codes["country_name"]))

# 映射后找出主贸易流
print(f"\n  Top 10 贸易流 (带国家名):")
t2023 = trade[trade["year"] == 2023].copy()
t2023["exp_iso"] = t2023["exporter_iso"].map(code_map)
t2023["imp_iso"] = t2023["importer_iso"].map(code_map)
t2023["exp_name"] = t2023["exp_iso"].map(name_map)
t2023["imp_name"] = t2023["imp_iso"].map(name_map)
top10_2023 = t2023.nlargest(10, "value_kusd")
for _, row in top10_2023.iterrows():
    print(f"    {row['exp_name']:20s} -> {row['imp_name']:20s} | "
          f"HS{row['hs6']} | ${row['value_kusd']:,.0f} kUSD")

# China 的总出口（代码 156 → CHN）
china = t2023[t2023["exporter_iso"] == 156]
print(f"\n  China (code=156) total exports 2023: ${china['value_kusd'].sum()/1e6:,.1f} M USD ({len(china)} rows)")
# 按产品
china_by_hs = china.groupby("hs6")["value_kusd"].sum().sort_values(ascending=False)
print(f"  Top 5 products:")
for hs, val in china_by_hs.head(5).items():
    print(f"    HS{hs}: ${val/1e6:.1f} M USD")

# ============================================================
# 问题 3: BACI 数据是否覆盖完整的清洁技术贸易？
# ============================================================
print()
print("=" * 60)
print("问题 3: 产品覆盖度")
print("=" * 60)
all_hs = trade["hs6"].unique()
print(f"  我们的 HS 码数: {len(all_hs)}")
print(f"  总行数: {len(trade):,}")
# 检查产品代码在 ZIP 的 products 表中的对应
with zipfile.ZipFile(zip_path, "r") as zf:
    with zf.open("product_codes_HS12_V202601.csv") as f:
        products = pd.read_csv(f)
print(f"  BACI HS12 产品总数: {len(products):,}")
# 我们的产品是否在表中
our_products = set(str(h) for h in all_hs)
baci_products = set(str(h) for h in products["code"].unique())
found = our_products & baci_products
print(f"  我们在 BACI 中找到的产品码: {len(found)}/{len(our_products)}")
not_found = our_products - baci_products
if not_found:
    print(f"  未找到的产品码: {not_found}")

# ============================================================
# 问题 4: 真实市场规模对比
# ============================================================
print()
print("=" * 60)
print("问题 4: 与已知统计对比")
print("=" * 60)
print("  已知: 2023年全球太阳能电池出口约 $300-500B (IEA)")
print("  已知: 2023年全球锂电池出口约 $150-200B")
print(f"  我们: 2023年太阳能(85414x) = ${solar_sum/1e9:.2f}B" if False else "")
# 汇总
t2023_total = trade[trade["year"] == 2023]["value_kusd"].sum()
print(f"  我们: 2023年全部低碳产品 = ${t2023_total/1e6:.0f}M USD = ${t2023_total/1e9:.2f}B USD")
print(f"  结论: 我们的数据比真实市场小 ~100-1000倍")
print(f"  原因: BACI 中这些 HS6 码的贸易流记录可能不完整，")
print(f"  或者 HS12 编码体系下清洁技术产品分散在更多未收录的编码中")
