# Green Trade Trilemma

Code and data for "The Green Trade Trilemma: Measuring and Resolving the Tension Between Decarbonization Speed, Supply Chain Diversity, and Development Equity"

## Data

The low-carbon technology trade database is constructed from:

- **CEPII BACI HS12** (V202601): Download from https://www.cepii.fr/CEPII/en/bdd_modele/bdd_modele_item.asp?id=37
- **IRENA renewable capacity**: Via Our World in Data (CC-BY), https://ourworldindata.org/renewable-energy
- **World Bank WDI**: Free API, https://api.worldbank.org

Place the BACI zip file and extracted trade CSV in `data/raw/`.

The de-risking policy inventory (`data/raw/derisking_policy_inventory.csv`) and the analysis-ready panel (`data/processed/panel_analysis_ready.csv`) are included.

## Reproduction

```bash
pip install -r requirements.txt

# 1. Download and process data
python download_baci.py
python collect_data.py
python process_data.py

# 2. Run analyses
python did_analysis.py
python did_product_level.py
python cs_did_estimator.py
python structural_model.py

# 3. Generate figures and tables
python fig1_trilemma_framework_v13.py
python fig2_trade_network.py
python fig3_cs_did_event_study.py
python fig4_counterfactual_dotwhisker.py
python fig5_temporal_trends.py
python generate_extended_figures.py
python generate_supplementary.py
python generate_supp_methods.py
```

## License

MIT
