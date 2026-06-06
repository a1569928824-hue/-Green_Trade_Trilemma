#!/usr/bin/env python3
"""数据审计 v3 — 修复格式问题"""
import pandas as pd
import zipfile, os

RAW = r"F:\科研论文\投稿\Green_Trade_Trilemma_Proposal\data\raw"

# ============================================================
# 1. WDI 代码格式问题
# ============================================================
print("=" * 60)
print("1. WDI 数据代码格式")
print("=" * 60)
wdi = pd.read_csv(os.path.join(RAW, "worldbank_wdi.csv"))
codes = wdi["country_code"].dropna().astype(str).unique()
# 真正的国家代码是 2 字母 ISO alpha-2
iso2_codes = [c for c in codes if c.isalpha() and len(c) == 2]
agg_codes = [c for c in codes if not (c.isalpha() and len(c) == 2)]
print(f"  ISO2 国家码: {len(iso2_codes)} 个")
print(f"    示例: {iso2_codes[:20]}")
print(f"  聚合体码: {len(agg_codes)} 个")
print(f"    示例: {agg_codes[:10]}")
# 聚合体包括: 1A=Arab World, 1W=World, 4E=East Asia & Pacific, 7E=Europe & Central Asia 等
# 映射: CN → CHN, US → USA, DE → DEU 等
# 这部分需要修复！

# ============================================================
# 2. BACI 贸易值验证
# ============================================================
print()
print("=" * 60)
print("2. BACI 贸易数据验证")
print("=" * 60)
trade = pd.read_csv(os.path.join(RAW, "baci_low_carbon_trade.csv"))

# 单位: 千美元 (kUSD)
# value=1 → $1,000
print(f"  单位: 千美元 (kUSD)")
print(f"  Total (2012-2024): ${trade['value_kusd'].sum()/1e6:,.0f} M kUSD")
print(f"    = ${trade['value_kusd'].sum()*1000/1e9:,.1f} B USD (换算为美元)")

t2023 = trade[trade["year"] == 2023]
print(f"  2023 total: ${t2023['value_kusd'].sum()*1000/1e9:,.1f} B USD")

# 最大贸易流
t2023_sorted = t2023.sort_values("value_kusd", ascending=False)
print(f"\n  Top 10 贸易流 2023:")
for _, row in t2023_sorted.head(10).iterrows():
    print(f"    exp={int(row['exporter_iso']):4d} -> imp={int(row['importer_iso']):4d} | "
          f"HS{int(row['hs6'])} | ${row['value_kusd']*1000/1e9:.2f} B")

# 加载国家代码映射
zip_path = os.path.join(RAW, "BACI_HS12_V202601.zip")
with zipfile.ZipFile(zip_path, "r") as zf:
    with zf.open("country_codes_V202601.csv") as f:
        codes_df = pd.read_csv(f)
code_to_iso3 = dict(zip(codes_df["country_code"], codes_df["country_iso3"]))
code_to_name = dict(zip(codes_df["country_code"], codes_df["country_name"]))

# 映射
print(f"\n  Top 10 (带国名) 2023:")
for _, row in t2023_sorted.head(10).iterrows():
    exp_c = int(row['exporter_iso'])
    imp_c = int(row['importer_iso'])
    exp_name = code_to_name.get(exp_c, str(exp_c))
    imp_name = code_to_name.get(imp_c, str(imp_c))
    print(f"    {exp_name:25s} -> {imp_name:25s} | "
          f"HS{int(row['hs6'])} | ${row['value_kusd']*1000/1e9:.2f} B")

# China total
china_2023 = t2023[t2023["exporter_iso"] == 156]
china_total = china_2023["value_kusd"].sum() * 1000 / 1e9
total_2023 = t2023["value_kusd"].sum() * 1000 / 1e9
print(f"\n  China (code=156) 2023 清洁技术出口: ${china_total:.1f} B")
print(f"  中国份额: {china_total/total_2023*100:.1f}%")

# ============================================================
# 3. IRENA 数据验证
# ============================================================
print()
print("=" * 60)
print("3. IRENA/OWID 数据验证")
print("=" * 60)
cap = pd.read_csv(os.path.join(RAW, "irena_capacity.csv"))
# 与国际能源署已知数据对比
# IRENA Renewable Capacity Statistics 2025:
# China 2024: ~887 GW solar, ~521 GW wind
chn_cap = cap[(cap["country"] == "China") & (cap["year"] == 2024)]
for tech in chn_cap["technology"].unique():
    sub = chn_cap[chn_cap["technology"] == tech]
    val = sub["capacity_mw"].sum()
    print(f"  China 2024 {tech:20s}: {val/1e3:,.0f} GW")
# 这些数据应该与 IRENA 官方报告一致

# ============================================================
# 4. 政策数据来源审计
# ============================================================
print()
print("=" * 60)
print("4. 政策数据来源审计")
print("=" * 60)
policy = pd.read_csv(os.path.join(RAW, "derisking_policy_inventory.csv"))
print(f"  来源: 作者根据公开文献手动汇编 (NOT from API/database)")
print(f"  事件数: {len(policy)}")
print(f"  国家数: {policy['country'].nunique()}")
print(f"  年份: {policy['year'].min()}-{policy['year'].max()}")
print(f"  WARNING: 这47条政策基于文献知识整理，未经系统数据库验证")
print(f"  建议: 对照 WTO Trade Policy Review 和 IEA Policy Database 逐条核实")

# ============================================================
# 5. 出口管制数据来源审计
# ============================================================
print()
print("=" * 60)
print("5. 出口管制数据来源审计")
print("=" * 60)
export = pd.read_csv(os.path.join(RAW, "export_restrictions.csv"))
print(f"  来源: 作者根据新闻报道手动汇编")
print(f"  事件数: {len(export)}")
print(f"  WARNING: 未经系统验证")

# ============================================================
# 总结
# ============================================================
print()
print("=" * 60)
print("审计总结")
print("=" * 60)
print("""
  IRENA 容量数据:    [REAL] 来自 Our World in Data (OWID), 基于 IRENA 官方统计
  World Bank WDI:    [REAL] 来自 World Bank API, 但使用 alpha-2 码需映射
  BACI 贸易数据:     [REAL] 来自 CEPII BACI HS12 V202601, 官方学术数据库
  去风险政策:        [HAND-COMPILED] 基于文献知识, 需系统核实
  出口管制:          [HAND-COMPILED] 基于新闻报道, 需系统核实
""")
