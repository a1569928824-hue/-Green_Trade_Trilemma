
# Supplementary Methods

## Contents

1. [Data Construction Details](#s1)
2. [Trilemma Index Construction](#s2)
3. [Difference-in-Differences Estimation](#s3)
4. [Bartik (Shift-Share) Instrument](#s4)
5. [Dekle-Eaton-Kortum Structural Model](#s5)
6. [Counterfactual Scenario Specification](#s6)
7. [Robustness Checks](#s7)
8. [Extended Data Figure Descriptions](#s8)

---

<a name="s1"></a>
## 1. Data Construction Details

### 1.1 Low-carbon technology trade database

The bilateral trade database is constructed from CEPII BACI HS12 (version V202601), which
provides reconciled bilateral trade flows at the HS 6-digit level for the period 2012-2024.
BACI improves on raw UN Comtrade by reconciling mirror flows: when country A reports
exporting value V to country B, but country B reports importing value V' from country A,
BACI uses an econometric reconciliation procedure to produce a single consistent estimate.
This is particularly valuable for developing-country trade flows, where reporting quality
varies substantially.

The product classification follows three established lists:

1. **OECD Combined List of Environmental Goods (CLEG)**: A comprehensive taxonomy of
   environmental goods, including renewable energy equipment.

2. **WTO Environmental Goods Agreement (EGA) negotiating list**: The 2016 list of products
   identified for tariff elimination on environmental goods.

3. **APEC List of Environmental Goods (2012)**: The Asia-Pacific Economic Cooperation
   list of 54 environmental goods.

From these lists, we identify 124 HS 2012 6-digit codes directly relevant to low-carbon
technology trade. These are organized into five technology groups (Supplementary Table S1):
solar photovoltaic systems (30 codes), wind power equipment (22 codes), lithium-ion battery
supply chain (27 codes), hydrogen and electrolyzer (17 codes), and smart grid and enabling
technologies (38 codes). Three codes (854142, 854143, 381800) are post-HS2012 additions and
do not appear in the 2012 BACI data; they are classified using available HS2017 concordance
tables where possible.

Non-sovereign entities are excluded from the analysis. We identify 45 territories,
dependencies, and special administrative regions that are separate reporting entities
in BACI but are not sovereign countries (e.g., Hong Kong SAR, Puerto Rico, Guam,
Bermuda). These are excluded to avoid double-counting of re-export hubs and to maintain
a consistent unit of analysis (sovereign countries). The final sample contains 223
sovereign countries.

### 1.2 Renewable energy capacity data

Installed capacity data (MW) for solar photovoltaic, wind, and geothermal electricity
generation are sourced from IRENA (International Renewable Energy Agency) via the
Our World in Data platform (CC-BY licensed, GitHub repository). Data cover 2015-2024.

**Hydropower exclusion**: Hydropower capacity data (in MW of installed capacity, as
distinct from electricity generation in TWh) are not consistently available from
official sources across all countries at the annual frequency required for the GSI
calculation. IRENA's data portal blocks automated programmatic access to detailed
country-level hydropower capacity data. The IEA database also restricts API access
to detailed hydropower statistics. While OWID publishes hydropower *generation* (TWh),
this cannot be directly converted to installed capacity without country-specific
capacity factors. Consequently, the GSI is based on Solar PV + Wind + Geothermal
capacity only. This covers the three technologies with the most dynamic recent
deployment and the clearest trade linkages to the HS6 product classification.

Key validation statistics (2024): China solar PV capacity 887 GW, China wind capacity
521 GW (cross-verified against IRENA Renewable Capacity Statistics 2025 official
publication).

### 1.3 De-risking policy inventory

The de-risking policy inventory identifies 47 distinct clean-tech trade policy
interventions across 32 countries over the period 2020-2024. Policies are identified
through systematic review of: (1) WTO Trade Policy Reviews, (2) national legislation
databases (U.S. Congress, EU EUR-Lex, India's Gazette of India, etc.), (3) IEA Policy
Database, (4) official government press releases, and (5) UNCTAD Trade and Environment
Review.

Each policy is coded with:
- **Country** and **year** of implementation
- **Policy type** (tariff, local content requirement, anti-subsidy duty, export control, investment screen)
- **Tariff rate** (percentage points, if applicable)
- **Local content requirement** (percentage, if applicable)
- **Products covered** (percentage of 124-product basket, estimated)
- **De-risking intensity** (composite index: 0 = no policy, 1 = maximum intensity)
- **Source reference** (official government document identifier)

All 47 events are documented with official government sources. A separate database of
7 export restriction events (China: 6 events on rare earths, polysilicon, graphite,
gallium/germanium, antimony, and permanent magnet technology; Indonesia: 1 event on
nickel ore) is maintained with similar documentation.

---

<a name="s2"></a>
## 2. Trilemma Index Construction

### 2.1 Green Speed Index (GSI)

The GSI for country $i$ in year $t$ is defined as:

$$GSI_{it} = \frac{D_{it} / D_{i,2015}}{\overline{(D_{jt} / D_{j,2015})}}$$

where $D_{it}$ is the total installed capacity (MW) of solar PV, wind, and geothermal
electricity generation in country $i$ in year $t$, and the denominator is the
cross-country average of the same ratio in year $t$.

**Baseline floor**: $D_{i,2015}$ is floored at 10 MW. This prevents small-baseline
inflation: a country with 1 MW of solar in 2015 that adds 10 MW by 2024 would have
an 11-fold increase, dominating the index even though the absolute deployment is
modest. The 10 MW threshold is approximately the capacity of a single utility-scale
solar installation; countries below this threshold are primarily small island states
and least-developed countries with minimal clean-energy deployment.

**Winsorization**: The raw GSI is Winsorized at the 99th percentile to limit the
influence of extreme values, rather than using a fixed ceiling. The P99 threshold
varies by year, ranging from approximately 8.5 to 13.9.

**Normalization**: Because the empirical GSI distribution is heavily right-skewed
(skewness > 6), we apply a logarithmic transformation before min-max scaling:

$$GSI^{log}_{it} = \ln(GSI_{it})$$

$$GSI^{norm}_{it} = (GSI^{log}_{it} - GSI^{log}_{min}) / (GSI^{log}_{max} - GSI^{log}_{min})$$

The min-max scaling uses the global minimum and maximum across all countries and
years to preserve cross-sectional and temporal comparability.

### 2.2 Green Diversity Index (GDI)

$$GDI_{it} = 1 - \sum_k s_{ikt}^2$$

where $s_{ikt} = M_{ikt} / \sum_k M_{ikt}$ is the share of exporting country $k$ in
country $i$'s total imports of the 124 low-carbon technology products in year $t$,
measured by value (current kUSD).

GDI ranges from 0 (all imports from a single source) to $1 - 1/K$ (imports evenly
distributed across $K$ sources). It is normalized to [0,1] using global min-max scaling
across all countries and years.

### 2.3 Green Equity Index (GEI)

$$GEI_{it} = \frac{\sum_{k \in Developing} M_{ikt}}{\sum_k M_{ikt}}$$

where $M_{ikt}$ is country $i$'s imports of low-carbon technology products from
exporting country $k$ in year $t$, and the "Developing" classification follows the
World Bank country income classification (low-income and middle-income countries,
as of fiscal year 2025). GEI captures the share of each importing country's clean-tech
purchases that originates in developing-country exporters.

This formulation represents a departure from earlier single-global-time-series
approaches. By computing GEI at the country-year level, it gains cross-sectional
variation and can be included as an outcome variable in country-level panel regressions.

For aggregate analysis, we also compute:

$$GEI^{global}_t = \frac{\sum_{i \in Developing} X_{it}}{\sum_i X_{it}}$$

where $X_{it}$ is total low-carbon technology exports of country $i$ in year $t$.

---

<a name="s3"></a>
## 3. Difference-in-Differences Estimation

### 3.1 Country-level specification

Our baseline specification is a two-way fixed-effects (TWFE) model:

$$Y_{it} = \alpha + \beta \cdot DeRisk_{it} + \gamma \cdot X_{it} + \mu_i + \lambda_t + \varepsilon_{it}$$

estimated on an unbalanced panel of 223 countries over 2015-2024 (N = 2,682 country-year
observations). $DeRisk_{it}$ is either (a) a continuous policy intensity index (sum of
de-risking intensity across all policies active in country $i$ in year $t$) or (b) a binary
indicator for whether country $i$ has any de-risking policy active in year $t$. $X_{it}$
includes time-varying controls: log GDP per capita, manufacturing value-added share of GDP,
and renewable electricity share. $\mu_i$ and $\lambda_t$ are country and year fixed effects.
Standard errors are clustered at the country level.

### 3.2 Event-study specification

We estimate dynamic treatment effects using a binned event-study specification:

$$Y_{it} = \sum_{k=-4, k\neq -1}^{+4} \beta_k \cdot 1\{t - t_i^* = k\} + \gamma \cdot X_{it} + \mu_i + \lambda_t + \varepsilon_{it}$$

where $t_i^*$ is the year of first de-risking policy adoption for country $i$, and
$1\{\cdot\}$ are event-time indicators. Event times are binned at the endpoints: all
periods 4 or more years before adoption are binned at $k = -4$, and all periods 4 or
more years after adoption are binned at $k = +4$. The reference period is $k = -1$
(one year before adoption). Coefficients $\beta_k$ trace the dynamic effect of
de-risking over event time.

### 3.3 Placebo tests

We conduct placebo tests by randomly assigning treatment timing to untreated countries
(100 draws). For each draw, we estimate the treatment effect and construct the
distribution of placebo estimates. The actual estimate is compared to this distribution:
if the actual estimate lies within the central 95% of the placebo distribution, we
cannot reject the null that the estimated effect is indistinguishable from random
variation.

### 3.4 Multiple time periods

For staggered difference-in-differences designs with multiple time periods and
variation in treatment timing, the standard TWFE estimator can produce biased
estimates when treatment effects are heterogeneous across cohorts or over time,
due to negative weighting of some cohort-time cells. We address this concern through:
(1) event-study visualization to assess pre-trends and treatment effect dynamics,
(2) placebo tests to assess whether effects are distinguishable from random variation,
and (3) reporting both continuous and binary treatment definitions. We note that the
limited number of treated units (32 countries, with only 20 adopting policies after
2020) and short post-treatment window (2020-2024) constrain the application of more
recent estimators such as Callaway-Sant'Anna or Sun-Abraham.

---

<a name="s4"></a>
## 4. Bartik (Shift-Share) Instrument

### 4.1 Construction

The product-level analysis exploits within-product variation in de-risking exposure.
We construct a Bartik (shift-share) instrument as follows:

1. **Share component**: For each importer-product pair, we compute the pre-existing
   China import share, defined as the share of China in that importer's total imports
   of the product over the pre-policy period (2015-2019):

   $$z_{ip} = \frac{\sum_{t=2015}^{2019} M_{ip,CHN,t}}{\sum_{t=2015}^{2019} \sum_k M_{ip,k,t}}$$

2. **Shift component**: For each importer-year, we compute the de-risking policy
   intensity $P_{it}$ (continuous) or a post-policy indicator $Post_{it}$ (binary).

3. **Instrument**: $B_{ipt} = z_{ip} \times P_{it}$ (continuous) or $B_{ipt} = z_{ip} \times Post_{it}$ (binary).

### 4.2 Identification

The Bartik instrument isolates the component of de-risking exposure that is driven
by pre-existing supply chain structure ($z_{ip}$, determined before the main de-risking
wave) rather than contemporaneous economic conditions. The identifying assumption is
that, conditional on importer, year, and product fixed effects, pre-existing China
import shares affect changes in outcomes only through their interaction with
de-risking policies (exclusion restriction).

The first stage is very strong: $F = 104,125$, reflecting the mechanical relationship
between the pre-China share and policy exposure interacted with post-policy timing.
This is substantially above the Stock-Yogo critical value for 10% maximal IV bias
(approximately 16.38 for one endogenous regressor and one instrument).

### 4.3 Specification

**First stage**:
$$P_{ipt} = \pi \cdot B_{ipt} + \phi \cdot z_{ip} + \mu_i + \lambda_t + \nu_p + \eta_{ipt}$$

**Second stage**:
$$Y_{ipt} = \beta \cdot \widehat{P_{ipt}} + \phi \cdot z_{ip} + \mu_i + \lambda_t + \nu_p + \varepsilon_{ipt}$$

**Reduced form**:
$$Y_{ipt} = \rho \cdot B_{ipt} + \phi \cdot z_{ip} + \mu_i + \lambda_t + \nu_p + \varepsilon_{ipt}$$

where $\mu_i$, $\lambda_t$, and $\nu_p$ are importer, year, and product fixed effects
respectively. Standard errors are two-way clustered at the importer and product level.

The panel contains $N = 246,639$ observations (product $\times$ importer $\times$ year).

---

<a name="s5"></a>
## 5. Dekle-Eaton-Kortum Structural Model

### 5.1 Model setup

The structural analysis employs the Dekle-Eaton-Kortum (DEK) exact-hat algebra framework,
which solves for counterfactual equilibria in a multi-country Ricardian trade model
without requiring estimation of structural parameters such as absolute productivity
levels, iceberg trade costs, or bilateral preference parameters.

Consider $N$ countries, each producing a composite clean-technology good using a
continuum of intermediate inputs indexed by $\omega \in [0,1]$. Production of input
$\omega$ in country $i$ uses labor with productivity $z_i(\omega)$, drawn from a
Frechet distribution with shape parameter $\theta > 1$:

$$F_i(z) = \exp(-T_i z^{-\theta})$$

where $T_i$ is the country-specific average productivity (absolute advantage).

Inputs are traded subject to iceberg trade costs $\tau_{ij} \geq 1$, with $\tau_{ii} = 1$.
The price of input $\omega$ in destination $j$ is:

$$p_j(\omega) = \min_i \left\{ \frac{\tau_{ij} w_i}{z_i(\omega)} \right\}$$

where $w_i$ is the wage in country $i$.

Under the Frechet assumption, the share of country $j$'s expenditure allocated to
goods from country $i$ is:

$$\pi_{ij} = \frac{T_i (w_i \tau_{ij})^{-\theta}}{\sum_k T_k (w_k \tau_{kj})^{-\theta}} = \frac{T_i (w_i \tau_{ij})^{-\theta}}{\Phi_j}$$

where $\Phi_j = \sum_k T_k (w_k \tau_{kj})^{-\theta}$.

The price index in country $j$ is:

$$P_j = \gamma \Phi_j^{-1/\theta}$$

where $\gamma$ is a constant.

### 5.2 Exact-hat algebra

In the DEK approach, we express the model in terms of *changes* between the baseline
and counterfactual equilibria, denoted by hats ($\hat{x} = x'/x$). The baseline trade
shares $\pi_{ij}$ are observed in the data. The system is:

**Trade share changes**:
$$\hat{\pi}_{ij} = \frac{(\hat{w}_i \hat{\tau}_{ij})^{-\theta}}{\sum_k \pi_{kj} (\hat{w}_k \hat{\tau}_{kj})^{-\theta}}$$

**Price index changes**:
$$\hat{P}_j = \left(\sum_i \pi_{ij} (\hat{w}_i \hat{\tau}_{ij})^{-\theta}\right)^{-1/\theta}$$

**Balanced trade condition** (or goods market clearing):
$$\hat{w}_i Y_i = \sum_j \hat{\pi}_{ij} \pi_{ij} \hat{w}_j Y_j$$

where $Y_j$ is total expenditure on clean-tech goods in country $j$ (treated as
exogenous in the baseline specification).

This system of $N$ equations determines the $N$ wage changes $\hat{w}_i$ given
the vector of trade cost shocks $\hat{\tau}_{ij}$ and the observed baseline shares
$\pi_{ij}$.

### 5.3 Solution algorithm

The system is solved by iteration:

1. Initialize $\hat{w}_i^{(0)} = 1$ for all $i$.
2. Compute $\hat{P}_j^{(s)}$ using current $\hat{w}_i^{(s)}$.
3. Compute $\hat{\pi}_{ij}^{(s)}$ using current $\hat{w}_i^{(s)}$ and $\hat{\tau}_{ij}$.
4. Update $\hat{w}_i^{(s+1)}$ from the goods market clearing condition.
5. Apply damping: $\hat{w}_i^{(s+1)} \leftarrow \omega \hat{w}_i^{(s+1)} + (1-\omega) \hat{w}_i^{(s)}$ with $\omega = 0.3$.
6. Repeat until $\max_i |\hat{w}_i^{(s+1)} - \hat{w}_i^{(s)}| < 10^{-8}$.

The algorithm typically converges within 200-500 iterations for the scenarios
considered in this paper.

### 5.4 Calibration

The model is calibrated to the year 2024. The bilateral trade matrix $\pi_{ij}$
is computed from the BACI clean-tech trade data aggregated across all 124 HS6
codes. The model covers $N = 40$ countries, chosen to account for over 95% of
global clean-tech imports and exports. A rest-of-world aggregate absorbs the
remaining trade flows.

The trade elasticity $\theta = 4.2$ is our preferred estimate, obtained from the
cross-sectional relationship between clean-tech bilateral trade shares and tariff
variation in the pre-de-risking period (2015-2019). This estimate lies within the
range of trade elasticities typically used in the quantitative trade literature
(Head and Mayer, 2014, report a median estimate of 4.5 across gravity equation
studies).

Sensitivity analysis is conducted over $\theta \in \{2.5, 3.5, 4.2, 5.5, 6.5\}$
(Extended Data Figure 6).

### 5.5 Trilemma outcomes from the model

After solving for counterfactual wages and prices, we compute:

- **GSI**: $1 + \Delta \text{Welfare}_i$, where $\Delta \text{Welfare}_i = \hat{w}_i / \hat{P}_i - 1$ (real income gain from trade)
- **GDI**: $1 - \sum_k s_{ik}^2$, where $s_{ik} = \pi_{ik}$ are import shares in the counterfactual equilibrium
- **GEI**: $\sum_{i \in Developing} \tilde{X}_i / \sum_i \tilde{X}_i$, where $\tilde{X}_i = \sum_j \tilde{\pi}_{ij} \tilde{w}_j Y_j$ is counterfactual exports

All outcomes are reported as percentage changes from the BAU baseline in Figure 4
and Supplementary Table S7.

---

<a name="s6"></a>
## 6. Counterfactual Scenario Specification

**Scenario 1 (Business as Usual)**: All parameters at calibrated values. Existing
de-risking policies maintained at current levels, with no additional measures introduced.

**Scenario 2 (Full Decoupling)**: Trade costs on Chinese exports to high-income
countries are tripled. Implemented as $\hat{\tau}_{China,j} = 3.0$ for all
$j \in \text{High-income}$, representing a severe but not complete decoupling.

**Scenario 3 (CBAM Extension)**: A carbon price of $100/\text{tCO}_2$ applied to
all imports. The trade cost shock for each bilateral pair is proportional to the
difference in grid emission intensity between the exporter and importer:
$\hat{\tau}_{ij} = 1 + \eta \cdot (E_i - E_j) \cdot \$100/\text{tCO}_2$, where
$E_i$ is the grid emission intensity (tCO$_2$/MWh) in country $i$ and $\eta$ is
the emission intensity of the traded good.

**Scenario 4 (Climate Club, G7 + China)**: Club members (G7 countries + China)
apply zero tariffs on clean-tech trade among themselves and a common external tariff
of 10% on non-member imports. Non-members face most-favored-nation (MFN) tariff rates.
The MFN tariff change for club members is approximately +2.3 percentage points
for clean-tech products.

**Scenario 5 (Inclusive Green Trade)**: Climate Club framework (Scenario 4) augmented
with: (a) technology transfer that reduces the cost of importing from developing
countries by 15% through licensing and know-how sharing ($\hat{\tau} = 0.85$
for developing-country exporters), and (b) concessional finance that reduces trade
costs to developing countries by 7%, modeled as $\hat{\tau} = 0.93$ for imports
to developing countries.

**Scenario 6 (China Export Restrictions)**: China imposes export licensing requirements
on solar-grade polysilicon, rare-earth permanent magnets, and battery-grade lithium.
Implemented as $\hat{\tau}_{China,j} = 2.0$ (doubling effective export costs
for the affected product categories) for all importing countries $j$.

---

<a name="s7"></a>
## 7. Robustness Checks

### 7.1 Alternative de-risking intensity weights

We test three alternative weighting schemes for the de-risking intensity index:
(1) equal weights for tariff, local-content, and product-coverage components;
(2) principal component weights (first principal component); and (3) maximum
component only. Results are qualitatively unchanged across weighting schemes.

### 7.2 Leave-one-out analysis

We re-estimate the DID specifications excluding each treated country one at a time.
No single country drives the results; the coefficient on de-risking intensity
remains within one standard error of the baseline estimate in all cases.

### 7.3 Alternative product baskets

We re-estimate using three alternative product definitions: (a) the original
48-product OECD CLEG classification only, (b) the full 124-product classification,
and (c) a narrow 30-product "core clean-tech" definition limited to solar modules,
wind turbines, and lithium-ion batteries. Results are qualitatively robust across
definitions.

### 7.4 Alternative fixed-effects structures

We estimate specifications with: (a) country and year fixed effects (baseline),
(b) country and country-specific linear trends, (c) region-year interactive fixed
effects, and (d) income-group-year interactive fixed effects. Results are stable
across fixed-effects structures.

### 7.5 Heterogeneity by income group

We split the sample into high-income and developing countries (World Bank
classification). We find no statistically significant differences in the
treatment effect across income groups for any of the three outcomes. This
null result is consistent with the overall finding of limited country-level
effects from de-risking policies over the 2020-2024 period.

### 7.6 Heterogeneity by product group

We estimate product-level regressions separately for solar PV, wind, battery,
smart grid, and other products. We find no significant differences in the
direction or magnitude of the de-risking effect on import unit values across
technology groups. This suggests that the cost effects of de-risking are not
concentrated in particular technology categories.

### 7.7 Sensitivity of DEK results to trade elasticity

We re-solve the structural model for $\theta \in \{2.5, 3.5, 4.2, 5.5, 6.5\}$.
The qualitative pattern of results is unchanged: Scenario 5 (Inclusive Green Trade)
remains the only configuration that improves all three trilemma dimensions
simultaneously across all values of $\theta$ (Extended Data Figure 6). The
magnitude of the effects increases as $\theta$ decreases (higher trade elasticity
implies larger responses to trade cost changes), but the ranking of scenarios
is preserved.

---

<a name="s8"></a>
## 8. Extended Data Figure Descriptions

**Extended Data Figure 1**: China's export share by technology group, 2015-2024.
Line plot showing China's share of global exports (by value) for solar PV, wind,
battery, smart grid, and other clean-tech products. The dashed vertical line at
2020 marks the onset of major de-risking policies.

**Extended Data Figure 2**: Placebo tests. Histograms of DID coefficient estimates
from 100 random assignments of treatment timing to untreated countries, for each
of the three outcome variables (GDI, GEI, GSI). The dashed vertical line shows
the actual estimate.

**Extended Data Figure 3**: Clean-tech trade composition and GSI distribution.
Left panel: stacked area chart of global clean-tech trade value by technology
group (solar PV, wind, battery). Right panel: histogram of GSI values across
active countries in 2024.

**Extended Data Figure 4**: Pairwise correlations among trilemma dimensions, 2024.
Three scatter plots for active countries (>100 MW installed capacity): GSI vs GDI,
GSI vs GEI, and GDI vs GEI. Linear fits and Pearson correlation coefficients
are shown.

**Extended Data Figure 5**: Bartik first-stage relationship. Bar chart of mean
policy intensity by bins of pre-existing China import share (2015-2019 average),
illustrating the first-stage relationship underlying the Bartik instrument.

**Extended Data Figure 6**: Sensitivity of DEK counterfactual results to the trade
elasticity $\theta$. Bar charts showing percentage changes from BAU in GSI, GDI,
and GEI across four scenarios, for five values of $\theta$ ranging from 2.5 to 6.5.

**Extended Data Figure 7**: Trilemma index trends by income group, 2015-2024.
Time series of mean GSI, GDI, and GEI for high-income vs developing countries,
showing the divergence in trilemma outcomes across income groups.

**Extended Data Figure 8**: Top 25 HS6 products by global trade value, 2015-2024.
Horizontal bar chart ranking the most traded products in the clean-tech basket.

**Extended Data Figure 9**: Clean-tech import cost trends for ever-treated vs
never-treated countries, 2015-2024. Weighted average unit values (kUSD/ton) over
time, showing that pre-treatment trends are broadly similar across groups.
