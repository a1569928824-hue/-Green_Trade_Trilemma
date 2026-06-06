#!/usr/bin/env python3
"""
下载并过滤 CEPII BACI 双边贸易数据
======================================
BACI HS12 覆盖 2012-2024，HS6 级别，无需注册。
只保留低碳技术相关 HS6 码，大幅缩减文件大小。
"""
import os
import sys
import zipfile
import csv
import io
import requests
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

# 低碳技术 HS6 码（基于 OECD CLEG + WTO EGA + APEC 清单）
# 参考文献: OECD (2023) Combined List of Environmental Goods;
#           WTO (2016) Environmental Goods Agreement Negotiating List;
#           APEC (2012) List of Environmental Goods
LOW_CARBON_HS = {
    # ===========================================
    # Group 1: Solar Photovoltaic Systems (30 codes)
    # ===========================================
    # --- Polysilicon & wafers ---
    "280461",  # Silicon containing ≥99.99% (polysilicon)
    "281122",  # Silicon dioxide
    "381800",  # Doped silicon wafers for PV cells
    # --- PV cells & modules ---
    "854140",  # Photosensitive semiconductor devices (PV cells)
    "854142",  # PV cells not assembled into modules
    "854143",  # PV cells assembled into modules/panels
    "854190",  # Parts of PV cells/modules
    # --- Inverters & power electronics ---
    "850440",  # Static converters (inverters)
    "850490",  # Parts for static converters
    # --- Glass & encapsulation ---
    "700719",  # Tempered safety glass (PV cover glass)
    "700729",  # Laminated safety glass
    "392010",  # PE film (encapsulant)
    "391990",  # Self-adhesive plastic sheets/film
    "900190",  # Optical elements (concentrators)
    "900290",  # Mirrors/reflectors (CSP)
    # --- Mounting structures ---
    "760611",  # Aluminum plates/sheets (frames)
    "760429",  # Aluminum alloy profiles (mounting rails)
    "761090",  # Aluminum structures (racking)
    "761699",  # Aluminum articles (mounting hardware)
    "730890",  # Steel structures (ground mounts)
    # --- Tracking & control ---
    "850131",  # DC motors ≤750W (trackers)
    "850132",  # DC motors >750W (large trackers)
    "853710",  # Control panels ≤1kV (MPPT/controllers)
    "903289",  # Automatic regulating/controlling instruments
    "903220",  # Thermostats
    # --- Cabling & connectors ---
    "741300",  # Copper stranded wire/cables (DC cabling)
    "854442",  # Electric conductors with connectors (MC4 etc.)
    "853690",  # Electrical connectors/junction boxes
    # --- Lighting ---
    "940540",  # LED lighting fixtures (solar integrated)

    # ===========================================
    # Group 2: Wind Power Equipment (22 codes)
    # ===========================================
    # --- Turbines & generators ---
    "850231",  # Wind-powered generating sets
    "850164",  # AC generators >750 kVA
    "850300",  # Parts for electric motors/generators (rotors/stators)
    # --- Drive train ---
    "848210",  # Ball bearings
    "848220",  # Tapered roller bearings
    "848230",  # Spherical roller bearings
    "848250",  # Cylindrical roller bearings
    "848280",  # Other bearings including combined
    "848310",  # Transmission shafts (main shaft)
    "848340",  # Gearboxes/speed changers
    "848360",  # Clutches and shaft couplings
    # --- Towers ---
    "730820",  # Towers and lattice masts (turbine towers)
    "681091",  # Prefabricated structural components
    # --- Nacelle components ---
    "841280",  # Other engines (yaw drives)
    "841290",  # Engine parts (pitch/yaw systems)
    "850140",  # AC motors single-phase (yaw motors)
    # --- Electrical ---
    "853720",  # Control panels >1kV (wind farm substation)
    "850421",  # Liquid dielectric transformers ≤650 kVA
    "850422",  # Transformers 650-10000 kVA
    "850423",  # Transformers >10000 kVA
    # --- Blades ---
    "392690",  # Plastic articles (GFRP/CFRP components)
    "681599",  # Articles of stone/minerals (carbon fiber)

    # ===========================================
    # Group 3: Li-ion Battery Supply Chain (27 codes)
    # ===========================================
    # --- Raw materials ---
    "250410",  # Natural graphite (anode material)
    "280490",  # Selenium
    "281520",  # Potassium hydroxide (electrolyte)
    "282520",  # Lithium oxide/hydroxide
    "282690",  # Lithium hexafluorophosphate & other fluoro salts
    "282731",  # Magnesium chloride
    "283010",  # Sodium sulfides
    "283691",  # Lithium carbonates
    "284160",  # Manganites/manganates (cathode precursors)
    "284290",  # Other inorganic salts
    "281820",  # Alumina (separator coating)
    "282590",  # Other inorganic bases (cobalt/nickel hydroxides)
    # --- Battery cells & packs ---
    "850650",  # Lithium primary batteries
    "850680",  # Other primary batteries
    "850760",  # Lithium-ion accumulators
    "850780",  # Other accumulators (solid-state)
    # --- Battery components ---
    "850790",  # Battery parts (separators/casings)
    "850720",  # Lead-acid accumulators (grid storage)
    # --- Battery manufacturing equipment ---
    "847982",  # Mixing/kneading machines (electrode slurry)
    "847989",  # Other machines (coating/calendering)
    "847990",  # Parts of machines
    # --- Cell packaging ---
    "392190",  # Other plastic sheets/film (pouch film)
    "760720",  # Aluminum foil backed (pouch cell)
    # --- Battery management ---
    "903180",  # Other measuring instruments (BMS testers)
    "854370",  # Other electrical equipment
    "903033",  # Electrical measurement instruments (battery testers)
    "853650",  # Switches (BMS relays)

    # ===========================================
    # Group 4: Hydrogen & Electrolyzer (17 codes)
    # ===========================================
    # --- Electrolysis ---
    "854330",  # Electroplating/electrolysis equipment
    "842139",  # Gas filtering/purification
    "841480",  # Air/gas compressors
    "841940",  # Distillation/rectification equipment
    "841960",  # Gas liquefaction equipment
    # --- Storage & transport ---
    "730900",  # Tanks for compressed/liquefied gas
    "731100",  # Containers for compressed gas (H2 cylinders)
    # --- Fuel cells ---
    "850680",  # Other primary batteries (fuel cells)
    "850300",  # Motor/generator parts
    # --- Analysis & monitoring ---
    "902710",  # Gas analyzers
    "902720",  # Chromatographs
    "902620",  # Pressure measurement
    "902610",  # Flow meters
    "902680",  # Other gas measurement instruments
    # --- Hydrogen-compatible equipment ---
    "841989",  # Industrial equipment (reformers/H2 generators)
    "841990",  # Parts of industrial equipment
    "848180",  # Valves (high-pressure hydrogen)

    # ===========================================
    # Group 5: Smart Grid & Enabling Technologies (38 codes)
    # ===========================================
    # --- Transformers & switchgear ---
    "850421",  # Liquid dielectric transformers ≤650 kVA
    "850422",  # Transformers 650-10000 kVA
    "850423",  # Transformers >10000 kVA
    "853521",  # Auto circuit breakers
    "853529",  # Other circuit breakers
    "853530",  # Isolating/make-and-break switches
    "853540",  # Lightning arresters/voltage limiters
    "853590",  # Other switching equipment >1kV
    # --- Smart meters & sensors ---
    "902830",  # Electricity meters (smart meters)
    "903031",  # Multimeters
    "903039",  # Other measurement instruments
    "903084",  # Instruments with recording device
    # --- Communication & control ---
    "851762",  # Communication equipment (smart grid comms)
    "903281",  # Hydraulic/pneumatic controllers
    # --- Cables & conductors ---
    "854420",  # Coaxial cable
    "854460",  # Electric conductors >1kV
    # --- Heat pumps & energy efficiency ---
    "841861",  # Heat pumps (compression)
    "841950",  # Heat exchange units
    "841990",  # Parts of heat exchangers
    # --- Solar thermal ---
    "841919",  # Solar water heaters
    # --- Turbines & engines ---
    "841181",  # Other gas turbines ≤5000 kW
    "841182",  # Gas turbines >5000 kW
    "841199",  # Gas turbine parts
    # --- Industrial efficiency ---
    "841780",  # Industrial/lab furnaces
    "850152",  # AC motors multi-phase >750W (industrial drives)
    # --- Precision tubes & steel ---
    "730431",  # Cold-drawn steel tubes
    "730441",  # Stainless steel tubes cold-drawn
    # --- Optical & analytical ---
    "901380",  # Optical devices (solar resource monitoring)
    "901390",  # Optical parts
    "902750",  # Other optical instruments (pyranometers)
    "902780",  # Other analytical instruments
    "903010",  # Radiation measurement
    "903090",  # Parts for radiation measurement
    # --- General ---
    "903190",  # Parts for measuring instruments
    "903300",  # Parts for chapter 90 instruments
    "841290",  # Engine/motor parts
    "853710",  # Control panels ≤1kV (energy management)
    "853720",  # Control panels >1kV (substation automation)
}

LOW_CARBON_HS_SET = LOW_CARBON_HS  # 已经是 set

# BACI HS12 下载
BACI_URL = "https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS12_V202601.zip"
ZIP_PATH = os.path.join(RAW_DIR, "BACI_HS12_V202601.zip")
OUT_PATH = os.path.join(RAW_DIR, "baci_low_carbon_trade.csv")


def download_with_progress(url, dest):
    """带进度条的下载"""
    resp = requests.get(url, stream=True, timeout=300)
    total = int(resp.headers.get("content-length", 0))
    downloaded = 0
    start_time = time.time()
    with open(dest, "wb") as f:
        for chunk in resp.iter_content(chunk_size=10 * 1024 * 1024):  # 10MB chunks
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                elapsed = time.time() - start_time
                speed = downloaded / elapsed / 1e6 if elapsed > 0 else 0
                pct = downloaded / total * 100 if total > 0 else 0
                eta = (total - downloaded) / (speed * 1e6) if speed > 0 else 0
                print(
                    f"\r  下载: {downloaded / 1e6:.0f}/{total / 1e6:.0f} MB "
                    f"({pct:.0f}%) {speed:.1f} MB/s ETA {eta:.0f}s",
                    end="",
                    flush=True,
                )
    print()
    return dest


def filter_baci_csv(zip_path, hs_codes, out_path):
    """
    从 BACI ZIP 中流式提取 CSV，只保留指定 HS6 码的行。

    BACI CSV 格式（无 header）:
    t,i,j,k,v,q
    t = 年份
    i = 出口国 ISO 3-digit code
    j = 进口国 ISO 3-digit code
    k = HS6 产品码
    v = 贸易值（千美元）
    q = 数量（吨）
    """
    print(f"  打开 ZIP: {zip_path}")
    with zipfile.ZipFile(zip_path, "r") as zf:
        # 找所有 CSV 文件（按年份拆分）
        csv_names = sorted([n for n in zf.namelist() if n.lower().endswith(".csv") and n.startswith("BACI_HS")])
        if not csv_names:
            raise ValueError("ZIP 中未找到 CSV 文件")
        print(f"  找到 {len(csv_names)} 个年份 CSV 文件")

        total_written = 0
        total_read = 0
        with open(out_path, "w", newline="", encoding="utf-8") as f_out:
            writer = csv.writer(f_out)
            # 写入 header
            writer.writerow(
                ["year", "exporter_iso", "importer_iso", "hs6", "value_kusd", "quantity_tons"]
            )
            for csv_name in csv_names:
                print(f"  处理: {csv_name}...", end=" ", flush=True)
                year_total = 0
                year_match = 0
                with zf.open(csv_name) as f_in:
                    text_io = io.TextIOWrapper(f_in, encoding="utf-8")
                    for line in text_io:
                        year_total += 1
                        total_read += 1
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split(",")
                        if len(parts) < 5:
                            continue
                        hs6 = parts[3]
                        if hs6 in hs_codes:
                            writer.writerow(parts[:6])
                            year_match += 1
                            total_written += 1
                print(f"{year_total:,} 行, 匹配 {year_match:,} ({year_match/max(year_total,1)*100:.1f}%)")
    return total_written


def main():
    print("=" * 60)
    print("下载 CEPII BACI HS12 低碳技术贸易数据")
    print("=" * 60)

    # 1. 下载
    if os.path.exists(OUT_PATH):
        print(f"  输出文件已存在: {OUT_PATH}")
        print(f"  删除后重新下载？删除此文件后重新运行即可。")
        import pandas as pd
        df = pd.read_csv(OUT_PATH)
        print(f"  现有 {len(df):,} 行")
        return

    if not os.path.exists(ZIP_PATH):
        print(f"  开始下载 BACI HS12 ({BACI_URL.split('/')[-1]})...")
        download_with_progress(BACI_URL, ZIP_PATH)
        print(f"  下载完成: {ZIP_PATH}")
    else:
        print(f"  ZIP 已存在: {ZIP_PATH}")

    # 2. 过滤提取
    print(f"\n  过滤低碳技术 HS6 码 ({len(LOW_CARBON_HS_SET)} 个)...")
    n = filter_baci_csv(ZIP_PATH, LOW_CARBON_HS_SET, OUT_PATH)

    if n > 0:
        import pandas as pd
        df = pd.read_csv(OUT_PATH)
        print(f"\n  保存: {OUT_PATH}")
        print(f"  统计: {len(df):,} 行")
        print(f"  年份: {df['year'].min()}-{df['year'].max()}")
        print(f"  出口国: {df['exporter_iso'].nunique()}")
        print(f"  进口国: {df['importer_iso'].nunique()}")
        print(f"  产品码: {df['hs6'].nunique()}")
        print(f"  总贸易额: {df['value_kusd'].sum() / 1e9:.1f} B USD")

    # 3. 可选：删除 ZIP（节省空间）
    # os.remove(ZIP_PATH)
    print("\n  提示: 下载的 ZIP 文件 (1.3GB) 可手动删除。过滤后的 CSV 已保留。")


if __name__ == "__main__":
    main()
