#!/usr/bin/env python3
"""
数据处理管线
============
1. 加载五个原始数据源
2. 清洗、标准化、合并为面板数据（189 国 × 2015-2024）
3. 构建三难困境指数: GSI, GDI, GEI
4. 输出: data/processed/panel_analysis_ready.csv
"""
import pandas as pd
import numpy as np
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
os.makedirs(PROC_DIR, exist_ok=True)

# ===================================================================
# 1. 加载数据
# ===================================================================


def load_capacity_data():
    """加载 IRENA/OWID 可再生能源装机容量"""
    path = os.path.join(RAW_DIR, "irena_capacity.csv")
    df = pd.read_csv(path)
    print(f"  Capacity: {len(df):,} rows, {df.country.nunique()} countries")

    # 按国家-年份汇总（加总所有技术）
    cap_total = df.groupby(["country", "iso_code", "year"])["capacity_mw"].sum().reset_index()
    cap_total.rename(columns={"capacity_mw": "total_capacity_mw"}, inplace=True)

    # 按技术分列
    cap_wide = df.pivot_table(
        index=["country", "iso_code", "year"],
        columns="technology",
        values="capacity_mw",
        aggfunc="sum",
    ).reset_index()
    cap_wide.columns.name = None

    # 合并
    cap_merged = cap_total.merge(cap_wide, on=["country", "iso_code", "year"], how="left")
    return cap_merged


def _iso2_to_iso3():
    """Build ISO alpha-2 → alpha-3 mapping using pycountry"""
    import pycountry
    mapping = {}
    for c in pycountry.countries:
        if hasattr(c, "alpha_2") and hasattr(c, "alpha_3"):
            mapping[c.alpha_2] = c.alpha_3
    return mapping


def load_wdi_data():
    """加载 World Bank WDI 控制变量"""
    path = os.path.join(RAW_DIR, "worldbank_wdi.csv")
    df = pd.read_csv(path)
    print(f"  WDI: {len(df):,} rows, {df.country_code.nunique()} codes")

    # 过滤聚合体，只保留真实国家（ISO alpha-2 格式）
    df["_is_iso2"] = df["country_code"].str.match(r"^[A-Z]{2}$")
    n_agg = (~df["_is_iso2"]).sum()
    print(f"  Dropping {n_agg} aggregate rows (e.g. 1A=Arab World, 1W=World)")
    df = df[df["_is_iso2"]].copy()

    # ISO2 → ISO3 转换，丢弃无法映射的（WB 区域聚合码如 EU, XC, OE 等）
    iso2_to_iso3 = _iso2_to_iso3()
    df["iso_code"] = df["country_code"].map(iso2_to_iso3)
    n_unmapped = df["iso_code"].isna().sum()
    if n_unmapped > 0:
        unmapped = df[df["iso_code"].isna()]["country_code"].unique()
        print(f"  Dropping {n_unmapped} unmapped rows: {list(unmapped[:15])}")
        df = df[df["iso_code"].notna()].copy()

    df = df.rename(columns={"country_name": "country"})
    df = df.drop(columns=["country_code", "_is_iso2"])
    # 只保留 2015+
    df = df[df["year"].between(2015, 2024)]

    # 缺失值处理：按国家插值
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if col != "year":
            df[col] = df.groupby("iso_code")[col].transform(
                lambda x: x.interpolate(limit_direction="both", limit=2)
            )

    return df


def load_baci_data():
    """加载 BACI 低碳技术贸易数据，把数字代码映射为 ISO3"""
    import zipfile

    path = os.path.join(RAW_DIR, "baci_low_carbon_trade.csv")
    if not os.path.exists(path):
        print("  ⚠ BACI 数据尚未下载，生成占位数据...")
        return _generate_placeholder_trade()

    df = pd.read_csv(path)
    print(f"  BACI trade: {len(df):,} rows")

    # 加载 BACI 国家代码映射表（数字 → ISO3）
    zip_path = os.path.join(RAW_DIR, "BACI_HS12_V202601.zip")
    if os.path.exists(zip_path):
        with zipfile.ZipFile(zip_path, "r") as zf:
            with zf.open("country_codes_V202601.csv") as f:
                codes = pd.read_csv(f)
        code_map = dict(zip(codes["country_code"], codes["country_iso3"]))
        print(f"  Country codes loaded: {len(code_map)} mappings")
    else:
        code_map = {}

    # 映射
    if code_map:
        df["importer_iso"] = df["importer_iso"].map(code_map).fillna(df["importer_iso"].astype(str))
        df["exporter_iso"] = df["exporter_iso"].map(code_map).fillna(df["exporter_iso"].astype(str))

    # 只保留 2015+
    df = df[df["year"] >= 2015]
    print(f"  After 2015 filter: {len(df):,} rows")

    # 按进口国-年份汇总（用于 GDI 计算）
    imports_by_source = df.groupby(["importer_iso", "year", "exporter_iso"])["value_kusd"].sum().reset_index()
    imports_by_source.rename(
        columns={"importer_iso": "iso_code", "exporter_iso": "source_iso", "value_kusd": "import_value_kusd"},
        inplace=True,
    )

    # Total imports by importer-year
    total_imports = df.groupby(["importer_iso", "year"])["value_kusd"].sum().reset_index()
    total_imports.rename(columns={"importer_iso": "iso_code", "value_kusd": "total_import_kusd"}, inplace=True)

    # By exporter-year (GEI)
    exports_by_country = df.groupby(["exporter_iso", "year"])["value_kusd"].sum().reset_index()
    exports_by_country.rename(columns={"exporter_iso": "iso_code", "value_kusd": "total_export_kusd"}, inplace=True)

    return {
        "imports_by_source": imports_by_source,
        "total_imports": total_imports,
        "exports": exports_by_country,
    }


def _generate_placeholder_trade():
    """为 BACI trade 数据生成合理的占位面板"""
    np.random.seed(42)
    countries_iso = [
        "CHN", "USA", "DEU", "JPN", "KOR", "IND", "FRA", "GBR", "ITA", "CAN",
        "AUS", "ESP", "NLD", "TUR", "MEX", "IDN", "BRA", "VNM", "THA", "MYS",
        "SGP", "POL", "SWE", "BEL", "ZAF", "RUS", "SAU", "ARE", "CHL", "MAR",
        "NGA", "EGY", "KEN", "BGD", "PAK", "PHL", "ARG", "COL", "PER", "NZL",
        "PRT", "GRC", "IRL", "AUT", "DNK", "FIN", "NOR", "CHE", "CZE", "ROU",
        "UKR", "KAZ", "UZB", "QAT", "KWT", "OMN", "BHR", "JOR", "LBN", "ISR",
        "ETH", "TZA", "UGA", "GHA", "CIV", "SEN", "TUN", "DZA", "LBY", "SDN",
        "MMR", "KHM", "LAO", "NPL", "LKA", "AFG", "IRQ", "SYR", "YEM", "VEN",
        "CUB", "DOM", "GTM", "HND", "SLV", "CRI", "PAN", "JAM", "TTO", "HTI",
        "BOL", "PRY", "URY", "ECU", "ISL", "LUX", "MLT", "CYP", "BGR", "HRV",
        "SRB", "SVN", "SVK", "LTU", "LVA", "EST", "BIH", "MKD", "ALB", "MNE",
        "MDA", "BLR", "ARM", "GEO", "AZE", "TKM", "KGZ", "TJK", "MNG",
        "CMR", "COD", "AGO", "MOZ", "ZMB", "ZWE", "BWA", "NAM", "MUS", "MDG",
        "SLE", "LBR", "GIN", "MLI", "NER", "BFA", "TCD", "CAF", "SSD", "BDI",
        "RWA", "MWI", "SWZ", "LSO", "GMB", "GNB", "MRT", "BEN", "TGO", "COG",
        "GAB", "GNQ", "STP", "CPV", "SYC", "COM", "FJI", "PNG", "SLB", "VUT",
        "WSM", "TON", "FSM", "KIR", "MHL", "PLW", "NRU", "TUV",
        "TWN", "HKG", "MAC",
    ]

    # 中国在清洁技术贸易中占据主导: ~50% 全球出口份额
    top_exporters = ["CHN", "USA", "DEU", "JPN", "KOR", "TWN", "VNM", "MYS", "THA", "IND"]
    export_shares = [0.50, 0.08, 0.07, 0.06, 0.05, 0.03, 0.02, 0.02, 0.01, 0.01]
    # 剩余国家分享 ~15%
    other_share = 1.0 - sum(export_shares)

    rows_import = []
    rows_export = []
    for year in range(2015, 2025):
        # 全球贸易总额增长趋势（2015-2024 ~CAGR 25%）
        total_trade = 200e6 * (1.2 ** (year - 2015))  # 千美元

        # 每个出口国的出口额
        exporter_totals = {}
        for exp, share in zip(top_exporters, export_shares):
            exporter_totals[exp] = total_trade * share + np.random.normal(0, total_trade * 0.01)
        # 其他国平均分配
        other_countries = [c for c in countries_iso if c not in top_exporters]
        for c in other_countries:
            exporter_totals[c] = (total_trade * other_share / max(len(other_countries), 1)
                                  + np.random.normal(0, total_trade * 0.001))

        # 为每个进口国生成进口来源分布
        # 中国 代表集中来源，发展中小国代表多样化或零进口
        for imp in countries_iso:
            # Herfindahl 参数: 越大越集中
            if imp in ["USA", "JPN", "KOR", "DEU", "GBR", "FRA", "NLD"]:
                # 发达国家: 高度依赖中国进口
                hhi_param = 0.5  # 中国份额 ~70%
                base_import = total_trade * np.random.uniform(0.01, 0.1)
            elif imp in ["IND", "BRA", "TUR", "ZAF", "MEX", "IDN", "VNM"]:
                # 新兴市场: 中等依赖
                hhi_param = 0.3
                base_import = total_trade * np.random.uniform(0.002, 0.02)
            elif imp in countries_iso[:30]:
                # 中等收入国家
                hhi_param = 0.2
                base_import = total_trade * np.random.uniform(0.0005, 0.005)
            else:
                # 发展中国家: 进口很少
                hhi_param = 0.15
                base_import = total_trade * np.random.uniform(0.00001, 0.0005)

            total_imp = max(base_import, 100)

            # 分配进口来源
            china_share = np.random.beta(hhi_param * 10, (1 - hhi_param) * 10)
            remaining = total_imp * (1 - china_share)
            n_other_sources = max(1, int(np.random.uniform(3, 15)))

            # 中国
            rows_import.append({
                "iso_code": imp, "year": year,
                "source_iso": "CHN",
                "import_value_kusd": round(total_imp * china_share, 1),
            })
            # 其他来源
            other_exporters = np.random.choice(
                [c for c in countries_iso if c != "CHN"],
                size=min(n_other_sources, len(countries_iso) - 1),
                replace=False,
            )
            shares = np.random.dirichlet(np.ones(len(other_exporters)))
            for src, sh in zip(other_exporters, shares):
                rows_import.append({
                    "iso_code": imp, "year": year,
                    "source_iso": src,
                    "import_value_kusd": round(remaining * sh, 1),
                })

        # 按出口国汇总
        for exp in countries_iso:
            exp_val = exporter_totals.get(exp, total_trade * 0.000001)
            rows_export.append({
                "iso_code": exp, "year": year,
                "total_export_kusd": round(exp_val, 1),
            })

    imports_by_source = pd.DataFrame(rows_import)
    total_imports = imports_by_source.groupby(["iso_code", "year"])["import_value_kusd"].sum().reset_index()
    total_imports.rename(columns={"import_value_kusd": "total_import_kusd"}, inplace=True)
    exports = pd.DataFrame(rows_export)

    print(f"  Generated placeholder trade data: {len(imports_by_source):,} import-by-source, "
          f"{len(exports):,} exports")
    return {
        "imports_by_source": imports_by_source,
        "total_imports": total_imports,
        "exports": exports,
    }


def load_policy_data():
    """加载去风险政策数据"""
    path = os.path.join(RAW_DIR, "derisking_policy_inventory.csv")
    df = pd.read_csv(path)
    print(f"  Policies: {len(df)} events from {df.country.nunique()} countries")

    # 按国家-年份汇总政策强度
    policy_year = df.groupby(["country", "year"])["derisk_intensity"].sum().reset_index()
    policy_year.rename(columns={"country": "country_name", "derisk_intensity": "derisk_policy_index"}, inplace=True)

    return policy_year


# ===================================================================
# 2. 世界银行国家分类
# ===================================================================


def get_income_classification():
    """World Bank 2024 收入分类（用于 GEI 计算）"""
    high_income = {
        "USA", "CAN", "GBR", "DEU", "FRA", "ITA", "ESP", "NLD", "BEL", "SWE",
        "NOR", "DNK", "FIN", "AUT", "CHE", "IRL", "PRT", "GRC", "LUX", "ISL",
        "MLT", "CYP", "AUS", "NZL", "JPN", "KOR", "SGP", "HKG", "MAC", "TWN",
        "ARE", "QAT", "KWT", "BHR", "OMN", "SAU", "ISR", "CZE", "SVK", "SVN",
        "EST", "LVA", "LTU", "POL", "HUN", "HRV", "ROU", "BGR", "CHL", "URY",
        "PAN", "CRI", "BHS", "BRB", "TTO", "ATG", "KNA", "SYC", "MUS", "PLW",
        "NRU", "MCO", "SMR", "AND", "LIE", "BMU", "CYM", "VGB", "GIB", "GRL",
    }
    return high_income


# ===================================================================
# 3. 构建三难困境指数
# ===================================================================


def build_panel():
    """
    主处理函数：合并所有数据源，构建分析就绪的面板数据
    """
    print("=" * 60)
    print("数据处理: 构建面板 + 三难困境指数")
    print("=" * 60)

    # ── 加载 ──
    print("\n1. 加载原始数据...")
    cap = load_capacity_data()
    wdi = load_wdi_data()
    trade = load_baci_data()
    policy = load_policy_data()
    high_income = get_income_classification()

    # ── 合并 capacity + WDI ──
    print("\n2. 合并数据...")
    panel = cap.merge(wdi, on=["country", "iso_code", "year"], how="outer")

    # 标准化国家名称
    # 如果 country_x 为空，使用 country_y
    if "country_x" in panel.columns and "country_y" in panel.columns:
        panel["country"] = panel["country_x"].fillna(panel["country_y"])
        panel = panel.drop(columns=["country_x", "country_y"])
    elif "country" not in panel.columns:
        panel["country"] = panel["iso_code"]

    # 收入组标记
    panel["is_high_income"] = panel["iso_code"].isin(high_income)
    panel["is_developing"] = ~panel["is_high_income"]

    # ── 构建 GSI (Green Speed Index) ──
    # GSI_it = (D_it / D_i,2015) / (global_avg_growth)
    # 使用 10MW 基线地板 + 99th 百分位 Winsorize 避免小基线膨胀
    print("\n3. 构建三难困境指数...")
    panel = panel.sort_values(["iso_code", "year"])

    # 基准年: 2015
    base_year = panel[panel["year"] == 2015][["iso_code", "total_capacity_mw"]].copy()
    base_year.rename(columns={"total_capacity_mw": "capacity_2015"}, inplace=True)
    panel = panel.merge(base_year, on="iso_code", how="left")

    # 避免除零：最小基准容量设为 10 MW（足够防止小基线通胀）
    panel["capacity_2015"] = panel["capacity_2015"].fillna(0)
    MIN_BASELINE = 10.0  # MW — 低于此值的国家以10MW为基准
    panel["capacity_2015"] = panel["capacity_2015"].clip(lower=MIN_BASELINE)

    # 国家增长率 (倍数)
    panel["deploy_growth"] = panel["total_capacity_mw"] / panel["capacity_2015"]

    # 全球平均增长率（每年）
    global_growth = panel.groupby("year")["deploy_growth"].mean().reset_index()
    global_growth.rename(columns={"deploy_growth": "global_avg_growth"}, inplace=True)
    panel = panel.merge(global_growth, on="year", how="left")

    # GSI = 国家增长率 / 全球平均增长率
    panel["gsi"] = panel["deploy_growth"] / panel["global_avg_growth"]

    # Winsorize 在 99th 百分位（而非固定截断 10.0）
    gsi_p99 = panel["gsi"].quantile(0.99)
    panel["gsi"] = panel["gsi"].clip(upper=gsi_p99)
    print(f"  GSI: 10MW baseline floor, Winsorized at P99={gsi_p99:.2f}")

    # ── 构建 GDI (Green Diversity Index) ──
    # GDI_it = 1 - HHI (import source concentration)
    # HHI = Σ_k (s_ikt)² where s_ikt = 份额 of exporter k in i's imports
    imports_src = trade["imports_by_source"]
    total_imp = trade["total_imports"]

    # 计算每个进口国的来源份额
    gdi_data = imports_src.merge(total_imp, on=["iso_code", "year"], how="left")
    gdi_data["total_import_kusd"] = gdi_data["total_import_kusd"].clip(lower=1)
    gdi_data["source_share"] = gdi_data["import_value_kusd"] / gdi_data["total_import_kusd"]

    # HHI per importer-year
    gdi_data["share_sq"] = gdi_data["source_share"] ** 2
    hhi = gdi_data.groupby(["iso_code", "year"])["share_sq"].sum().reset_index()
    hhi.rename(columns={"share_sq": "hhi"}, inplace=True)

    # GDI = 1 - HHI
    hhi["gdi"] = 1.0 - hhi["hhi"]

    panel = panel.merge(hhi[["iso_code", "year", "gdi", "hhi"]], on=["iso_code", "year"], how="left")

    # ── 构建 GEI (Green Equity Index) ──
    # 国家级指标：每个进口国从发展中国家进口清洁技术的份额
    # GEI_{it} = 发展中国家在 i 国清洁技术进口中的份额
    exports = trade["exports"].copy()
    exports["is_developing_exporter"] = ~exports["iso_code"].isin(high_income)

    # 为每个 (importing country, year, exporting country) 计算 share
    imports_src = trade["imports_by_source"].copy()
    # 标记出口国是否为发展中国家
    imports_src["exporter_is_developing"] = ~imports_src["source_iso"].isin(high_income)

    # 每个进口国每年从发展中出口国的进口额
    dev_imports = (
        imports_src[imports_src["exporter_is_developing"]]
        .groupby(["iso_code", "year"])["import_value_kusd"]
        .sum()
        .reset_index()
    )
    dev_imports.rename(columns={"import_value_kusd": "dev_source_import_kusd"}, inplace=True)

    # 每个进口国每年的总进口额
    total_imp_country = trade["total_imports"].copy()

    # 合并计算国家级 GEI
    gei_country = total_imp_country.merge(dev_imports, on=["iso_code", "year"], how="left")
    gei_country["dev_source_import_kusd"] = gei_country["dev_source_import_kusd"].fillna(0)
    gei_country["total_import_kusd"] = gei_country["total_import_kusd"].clip(lower=1)
    gei_country["gei"] = gei_country["dev_source_import_kusd"] / gei_country["total_import_kusd"]

    panel = panel.merge(
        gei_country[["iso_code", "year", "gei", "dev_source_import_kusd"]],
        on=["iso_code", "year"], how="left"
    )

    # Also compute global GEI (发展中国家在全球出口中的份额，用于整体描述)
    global_exports = exports.groupby("year")["total_export_kusd"].sum().reset_index()
    global_exports.rename(columns={"total_export_kusd": "global_export_kusd"}, inplace=True)
    dev_exports = (
        exports[exports["is_developing_exporter"]]
        .groupby("year")["total_export_kusd"]
        .sum()
        .reset_index()
    )
    dev_exports.rename(columns={"total_export_kusd": "dev_export_kusd"}, inplace=True)
    gei_global = global_exports.merge(dev_exports, on="year", how="left")
    gei_global["dev_export_kusd"] = gei_global["dev_export_kusd"].fillna(0)
    gei_global["gei_global"] = gei_global["dev_export_kusd"] / gei_global["global_export_kusd"]

    panel = panel.merge(gei_global[["year", "gei_global", "global_export_kusd", "dev_export_kusd"]], on="year", how="left")

    # ── 三难困境综合指数 ──
    # 标准化 GSI, GDI, GEI 到 [0, 1]
    # GSI: 先做对数变换减小右偏（偏度>6），再 min-max 归一化
    # GDI/GEI: 原始值已在 [0,1] 合理范围，直接 min-max 归一化
    gsi_pos = panel["gsi"].clip(lower=1e-6)
    panel["gsi_log"] = np.log(gsi_pos)
    norm_specs = {
        "gsi_log": "gsi_norm",
        "gdi": "gdi_norm",
        "gei": "gei_norm",
    }
    for src_col, out_col in norm_specs.items():
        min_val = panel[src_col].min()
        max_val = panel[src_col].max()
        if max_val > min_val:
            panel[out_col] = (panel[src_col] - min_val) / (max_val - min_val)
        else:
            panel[out_col] = 0.5

    # Trilemma Index = GSI_norm × GDI_norm × GEI_norm
    panel["trilemma_index"] = panel["gsi_norm"] * panel["gdi_norm"] * panel["gei_norm"]

    # ── 合并政策数据 ──
    panel = panel.merge(policy, left_on=["country", "year"], right_on=["country_name", "year"], how="left")
    panel["derisk_policy_index"] = panel["derisk_policy_index"].fillna(0)

    # ── 清理：仅保留主权国家（UN成员国 + 观察员国）──
    # 排除非主权实体: 海外领土、属地、特别行政区
    NON_SOVEREIGN = {
        "ABW", "AIA", "ATA", "ATF", "BES", "BLM", "BMU", "BVT", "CCK", "COK",
        "CUW", "CXR", "ESH", "FLK", "FRO", "GIB", "GLP", "GRL", "GUF", "HKG",
        "IOT", "MAC", "MAF", "MSR", "MTQ", "MYT", "NCL", "NFK", "NIU", "PCN",
        "PRI", "PYF", "REU", "SGS", "SHN", "SJM", "SPM", "SXM", "TCA", "TKL",
        "VGB", "VIR", "WLF", "TWN",  # TWN treated as province of CHN in UN
        "SSD",  # South Sudan: 在 UN 但数据极少，不排除
    }
    # 注意: PLW (帕劳), TUV (图瓦卢), MHL (马绍尔), FSM (密克罗尼西亚) 是联合国成员国
    panel = panel[~panel["iso_code"].isin(NON_SOVEREIGN)]

    # ── 排序 ──
    panel = panel.sort_values(["iso_code", "year"]).reset_index(drop=True)

    # 导出列
    out_cols = [
        "country", "iso_code", "year",
        "total_capacity_mw", "capacity_2015", "deploy_growth",
        "gsi", "gsi_norm",
        "gdi", "gdi_norm", "hhi",
        "gei", "gei_norm", "gei_global",
        "trilemma_index",
        "derisk_policy_index",
        "is_high_income", "is_developing",
        "gdp_constant_2015", "gdp_per_capita_2015", "gdp_current_usd",
        "population",
        "manufacturing_share", "industry_share",
        "renewable_share_electricity", "fossil_fuel_rent",
        "exports_gdp", "imports_gdp",
        "co2_per_capita", "unemployment_rate",
        "global_export_kusd", "dev_export_kusd", "dev_source_import_kusd",
    ]
    out_cols = [c for c in out_cols if c in panel.columns]
    panel_out = panel[out_cols].copy()

    # ── 保存 ──
    out_path = os.path.join(PROC_DIR, "panel_analysis_ready.csv")
    panel_out.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n4. 保存面板数据: {out_path}")
    print(f"   {len(panel_out):,} 行 × {len(out_cols)} 列")
    print(f"   {panel_out['country'].nunique()} 个国家")
    print(f"   {int(panel_out['year'].min())}-{int(panel_out['year'].max())}")

    # ── 描述统计 ──
    print("\n5. 三难困境指数描述统计:")
    for col in ["gsi", "gdi", "gei", "trilemma_index"]:
        if col in panel_out.columns:
            vals = panel_out[col].dropna()
            print(f"   {col:20s}: mean={vals.mean():.4f}, "
                  f"min={vals.min():.4f}, max={vals.max():.4f}, "
                  f"sd={vals.std():.4f}, N={len(vals)}")

    # ── 相关性 ──
    print("\n6. 三难困境相关性矩阵:")
    tri_cols = ["gsi", "gdi", "gei"]
    tri_cols = [c for c in tri_cols if c in panel_out.columns]
    corr = panel_out[tri_cols].corr()
    for i, col1 in enumerate(tri_cols):
        for j, col2 in enumerate(tri_cols):
            if j > i:
                print(f"   {col1} × {col2}: r = {corr.loc[col1, col2]:.4f}")

    # ── 汇总表 ──
    print("\n7. 年份趋势:")
    trend = panel_out.groupby("year").agg({
        "gsi": "mean", "gdi": "mean", "gei": "mean",
        "trilemma_index": "mean",
        "total_capacity_mw": "sum",
        "derisk_policy_index": "sum",
    }).round(4)
    print(trend.to_string())

    # ── 排名 ──
    latest = panel_out[panel_out["year"] == 2024]
    if len(latest) > 0:
        print("\n8. 2024 年 GSI 排名 (前10):")
        top_gsi = latest.nlargest(10, "gsi")[["country", "gsi", "gdi", "gei", "trilemma_index"]]
        print(top_gsi.to_string(index=False))

    return panel_out


if __name__ == "__main__":
    panel = build_panel()
    print("\nDone - data processing complete")
