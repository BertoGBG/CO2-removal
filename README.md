# Carbon Dioxide Removal (afforestation and perennialisation) input data for PyPSA-Eur and CO2 upstream emissions for 1st generation biofuels

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20798511.svg)](https://doi.org/10.5281/zenodo.20798511)

Archived on Zenodo: https://zenodo.org/records/20798511 (DOI: 10.5281/zenodo.20798511)

Reference: https://arxiv.org/abs/2603.25663

---

## Overview

This package provides the preprocessed input datasets for two Carbon Dioxide Removal (CDR)
technologies implemented in PyPSA-Eur, **Afforestation** and **Perennialisation**, and the
**upstream (cultivation) emissions of first-generation biofuels and unsustainable solid biomass**
(and the price of the latter) in PyPSA-Eur, extracted from the JRC ENSPRESO data.

## Changes

**v1.0.3**

* Upstream emissions of unsustainable biomass now count only what PyPSA-Eur does not already model:
  field N2O of the crop and the production of the imported share (30%) of the N fertiliser. Farm
  diesel and the European fertiliser production are left out, because PyPSA-Eur models the
  agriculture energy demand and the ammonia produced in Europe. The values come from the JRC
  input data of the RED default values (Edwards et al. 2019) instead of ENSPRESO Table 20:
  bioethanol 0.086 and biodiesel 0.062 tCO2eq/MWh (EU values). Unsustainable solid biomass keeps
  the full Table 20 willow factor: willow is hardly grown today, so its fertiliser and diesel are
  not in the historical demand modelled by PyPSA-Eur.
* New: `outputs/biomass_inputs/cultivation_emissions_1G.csv`, cultivation emissions of the 1G
  crops per MWh of crop (field N2O and imported N fertiliser separately) and the N fertiliser
  produced in Europe per MWh of crop, used by perennialisation in PyPSA-Eur (avoided ammonia
  demand, and the combination with the upstream emissions).

**v1.0.2** ([Zenodo 10.5281/zenodo.23341173](https://doi.org/10.5281/zenodo.23341173))

* Afforestation (growth method): the rotation age now counts only a share θ = 0.35 of the
  thinned volume (thinning-intensity dial), instead of full commercial thinning (θ = 1).
  The conifer/broadleaf split stays 50/50. The mean NUTS-2 rate rises from 4.28 to
  5.32 tCO₂ ha⁻¹ yr⁻¹; see [Methodology summary](#methodology-summary).
* New: method documentation `docs/afforestation_method.pdf`.
* New: JRC ENSPRESO biomass tables, ENSPRESO database costs, gap-filled per-country tables, and
  `outputs/biomass_inputs/unsustainable_biomass_upstream.csv` (upstream emission factors of
  unsustainable bioethanol, biodiesel and solid biomass, and the EU willow price), see
  [Biomass cost, emission and heating-value tables](#biomass-cost-emission-and-heating-value-tables-jrc-enspreso).

**v1.0.1**: afforestation (density and growth methods) and perennialisation inputs.

---

## Folder structure

```
scripts/
  afforestation/
    download_afforestation_data_avitabile.py   ← Method 1: download Figshare biomass densities
    download_zenodo_pilli_afforestation.py     ← Method 2: download Pilli JRC growth library
    download_fluxcom.py                        ← Method 2: download FluxCom GPP data
    01_compute_afforestation_rates_pilli.py    ← Method 2: compute rotation-averaged MAI per NUTS-2
    02_compute_nuts2_profiles.py               ← Method 2: compute monthly GPP seasonal profiles
    03_plot_check.py                           ← diagnostic plots
  perennialisation/
    download_eurostat_crops.py                 ← download Eurostat crop harvest data
  biomass_inputs/
    extract_enspreso_tables.py                 ← extract ENSPRESO cost, emission and heating-value tables
    fill_country_tables.py                     ← ENSPRESO database costs + fill missing countries
    compute_unsustainable_biomass_upstream.py  ← emission factors + price used by PyPSA-Eur
  run_all.py                                   ← run full pipeline end-to-end

data/
  fluxcom_raw/      ← FluxCom daily GPP NetCDF files (2010–2012, ~3.6 GB)
  nuts/             ← NUTS-2013 and NUTS-2021 boundary GeoJSON files
  biomass_inputs/   ← JRC ENSPRESO report (Ruiz et al. 2015) and ENSPRESO biomass database
  zenodo_Pilli/     ← Pilli et al. (2024) JRC forest growth library
    Volume_increment_database/     ← standing stock and NAI curves
    Volume_biomass_bcef_database/  ← BCEF lookup table
    Volume_biomass_selection/      ← auxiliary biomass selection tables

docs/
  afforestation_method.pdf  ← method documentation for the afforestation growth method

outputs/
  afforestation/    ← afforestation results (both methods)
  perennialisation/ ← Eurostat crop data (input for PyPSA-Eur)
  biomass_inputs/   ← ENSPRESO tables extracted from the JRC report (CSV)
```

## Quick start

To reproduce all outputs in one step:

```bash
python scripts/run_all.py
```

Individual steps can also be run in isolation — see the script docstrings for details.

---

# Afforestation datasets

Two independent methods are provided for deriving NUTS-2 afforestation CO₂ sequestration
rates. Both are available in PyPSA-Eur via the `afforestation[potential_type]` config key:
`"density"` for Method 1 and `"growth"` for Method 2.

## Method 1: Avitabile et al. biomass density dataset (direct download)

### Raw input

The dataset is downloaded directly from Figshare:

- URL: https://ndownloader.figshare.com/files/43678089
- Reference: Avitabile et al. (2024), *Scientific Data*, https://www.nature.com/articles/s41597-023-02868-8

Script: `scripts/afforestation/download_afforestation_data_avitabile.py`

### Output

* `outputs/afforestation/afforestation_nuts_biomass_densities.xlsx`
  Above-ground biomass density (t DM ha⁻¹) per NUTS-2 region, derived from the Avitabile
  et al. dataset. Used in PyPSA-Eur as the basis for the `"density"` sequestration rate.

---

## Method 2: Pilli et al. yield tables + FluxCom seasonal profiles

This is the recommended method described in the accompanying paper. It derives
rotation-averaged CO₂ sequestration rates from European forest inventory data and
distributes them across calendar months using observed Gross Primary Production (GPP).
A full methodological description is given in
[`docs/afforestation_method.pdf`](docs/afforestation_method.pdf) (A. Alamia, DTU Wind and Energy Systems,
13 October 2026), which documents exactly the outputs in this release.

### Data sources

#### Pilli et al. (2024) — JRC forest growth library

- **Zenodo**: https://zenodo.org/records/11387301
- **Reference**: Pilli, R., Blujdea, V., Rougieux, P. (2024). *JRC Forest Carbon Model calibration
  data for the period 2010–2020*. https://publications.jrc.ec.europa.eu/repository/handle/JRC135639
- **Downloaded to**: `data/zenodo_Pilli/`

The library provides age-class-resolved volume and increment curves for 222 forest types
across 25 EU Member States (EU-27 excluding Cyprus and Malta), derived from National Forest
Inventories. It includes:

  - **Standing stock** (m³ ha⁻¹): net merchantable volume by 10-year age class for even-aged stands.
  - **Net Annual Increment** (NAI, m³ ha⁻¹ yr⁻¹): harmonised volume growth rate by age class.
  - **Biomass Conversion and Expansion Factors** (BCEF, t_DM m⁻³): age-class-resolved factors
    converting merchantable volume to total aboveground dry biomass.

Script: `scripts/afforestation/download_zenodo_pilli_afforestation.py`

#### FluxCom RS+METEO — daily GPP (Jung et al., 2020)

- **Source**: anonymous FTP at `ftp.bgc-jena.mpg.de` (Max Planck Institute for Biogeochemistry)
- **Reference**: Jung, M. et al. (2020). *Biogeosciences*, 17(5), 1343–1365.
  https://doi.org/10.5194/bg-17-1343-2020
- **Files**: `GPP.RS_METEO.FP-ALL.MLM-ALL.METEO-ERA5.720_360.daily.{year}.nc`
  (years 2010–2012, ~1.2 GB/year, ~3.6 GB total)
- **Unit**: gC m⁻² day⁻¹ | Resolution: 0.5° global
- **Downloaded to**: `data/fluxcom_raw/`
- **Archived at**: https://doi.org/10.5281/zenodo.20798849 (CC-BY 4.0; not included in this
  git repository — too large for GitHub, see [Reproducibility note](#reproducibility-note))

Three years (2010–2012) are used to construct a stable climatological seasonal cycle.
The ERA5-forced ensemble was selected for consistency with the climate data used in PyPSA-Eur.

Script: `scripts/afforestation/download_fluxcom.py`

### Methodology summary

**Annual sequestration rates** (`01_compute_afforestation_rates_pilli.py`):

For each combination of forest type, NUTS-2 region, and management type, the optimal
rotation age T\* is the age that maximises the mean annual total production, within
25–100 years. Total production TP(T) = ∫₀ᵀ NAI dt includes the wood removed by thinning,
which the standing stock V(T) leaves out. Afforestation for carbon removal is thinned less
intensively than the commercial stands in the Pilli library, so only a share θ of the
thinned volume is counted:

```
TP_θ(T) = V(T) + θ × (TP(T) − V(T)),      θ = 0.35
T*      = argmax TP_θ(T) / T,             25 ≤ T ≤ 100 yr
```

θ = 1 is full commercial thinning (the v1.0.1 release) and θ = 0 locates T\* on the
standing stock alone. θ only moves T\*: the credited carbon is always the standing stock
at T\*, since only carbon that stays in the forest counts as removal. The
rotation-averaged CO₂ sequestration rate is:

```
MAI_CO2 = (V(T*) / T*) × BCEF(T*) × 0.5 × (44/12) × (1 + 0.25)
          [tCO₂ ha⁻¹ yr⁻¹]
```

where 0.5 is the IPCC carbon fraction, 44/12 is the CO₂-to-C molecular mass ratio,
and 0.25 is the root-to-shoot ratio. Only productive even-aged high-forest stands
(management types H, HP, HS, MAN) are included.

Per NUTS-2 region, MAI_CO2 is averaged with equal weight over the forest types of each
species group, and the conifer and broadleaf means are blended 50/50 (if only one group
has data, its mean is used). The 50/50 split meets the EU Biodiversity Strategy 2030 and
the national minimum broadleaf shares (20–30 %), and is conservative: a mix weighted
towards the more productive group would give slightly higher rates.

With θ = 0.35 the mean NUTS-2 rate is 5.32 tCO₂ ha⁻¹ yr⁻¹ (4.28 with θ = 1 in v1.0.1).
Other values can be computed with `--thinning-theta` (`--no-thinning` for θ = 0).

Regions not covered by the Pilli library (non-EU countries, small islands, city-states)
are filled via a cascade: NUTS-1 propagation → country-level propagation → distance-based
neighbour mean (≤100 km, iterated) → country mean → Mediterranean analogue for Malta and Cyprus.

**Monthly temporal profiles** (`02_compute_nuts2_profiles.py`):

For each NUTS-2 region, the 12-month GPP climatology (averaged over 2010–2012) is
aggregated from the 0.5° FluxCom grid using point-in-polygon assignment to NUTS-2013
boundaries, then normalised to unit sum. The monthly CO₂ sequestration rate is:

```
Rate_m,r = w_m,r × MAI_CO2,r     [tCO₂ ha⁻¹ month⁻¹]
```

where `w_m,r` are the normalised monthly GPP weights (sum to 1). Regions with no valid
GPP signal fall back to: neighbour mean (≤100 km) → country mean → uniform 1/12.

### Outputs

* `outputs/afforestation/afforestation_rates_per_forest_type.csv`
  Detailed per-forest-type rotation-averaged MAI_CO2 before NUTS-2 aggregation.

* `outputs/afforestation/afforestation_rates_nuts2.csv`
  NUTS-2 averaged sequestration rate for regions with direct Pilli library coverage.

* `outputs/afforestation/afforestation_rates_nuts2_full.csv`
  Full coverage: all ~320 NUTS-2 regions in the PyPSA-Eur model, with fallback values
  recorded per region. **Primary input for PyPSA-Eur** (`"growth"` method).

* `outputs/afforestation/afforestation_nuts2_monthly_weights.csv`
  12 normalised monthly GPP weights per NUTS-2 region (rows sum to 1).
  **Used by PyPSA-Eur** to set the time-varying efficiency of the afforestation Link.

* `outputs/afforestation/afforestation_nuts2_monthly_rates.csv`
  Monthly CO₂ sequestration rates (tCO₂ ha⁻¹ month⁻¹) per NUTS-2 region.

* `outputs/afforestation/fig_monthly_profiles_sample.png`
  Diagnostic figure: seasonal GPP profiles for a sample of NUTS-2 regions.

* `outputs/afforestation/fig_seasonal_map.png`
  Diagnostic map: spatial pattern of peak-month sequestration across Europe.

---

# Perennial crops and 1st-generation biofuels datasets

## Raw input

Crop harvest data are retrieved live from the **Eurostat API** (dataset `apro_cpshr`).
No preprocessing beyond format conversion is applied.

Script: `scripts/perennialisation/download_eurostat_crops.py`

## Outputs

* `outputs/perennialisation/eurostat_apro_cpshr_nuts2_raw.csv`
  Raw Eurostat crop harvest data at NUTS-2 resolution (dataset apro_cpshr, 2017–2020).
  **Used by PyPSA-Eur** as input for the perennialisation workflow.

* `outputs/perennialisation/eurostat_apro_cpshr_nuts0_raw.csv`
  Raw Eurostat crop harvest data at country (NUTS-0) resolution.
  **Used by PyPSA-Eur** as fallback for NUTS-2 regions with missing data.

---

# Biomass cost, emission and heating-value tables (JRC ENSPRESO)

## Raw input

Ruiz, P., Sgobbi, A., Nijs, W., Thiel, C., Dalla Longa, F., Kober, T., Elbersen, B., Hengeveld, G. (2015):
*The JRC-EU-TIMES model. Bioenergy potentials for EU and neighbouring countries.* EUR 27575 EN,
Publications Office of the European Union, doi:10.2790/39014.

File: `data/biomass_inputs/Ruiz2015_JRC-EU-TIMES_bioenergy_potentials_EUR27575.pdf`.
© European Union, 2015; reproduction is authorised provided the source is acknowledged.

## Method

`scripts/biomass_inputs/extract_enspreso_tables.py` reads the tables from the PDF text with
`pdfplumber` (no manual transcription): every data line starts with a country code followed by a
fixed number of values; `-` becomes empty (not available). Table 26 is a two-column list of
feedstocks and is parsed separately. Values are as printed in the report (medium scenario).

## Outputs

One CSV per table in `outputs/biomass_inputs/`, indexed by country code (36 countries, ENSPRESO
codes: `GR` for Greece, `UK` for the United Kingdom, `BH` for Bosnia and Herzegovina) unless noted:

| File | Report table | Content | Unit |
|------|--------------|---------|------|
| `table10_biofuel_crops.csv` | Table 10 | Cost of biofuel crops (sugar beet, oil crops, starchy crops), 2010/2030/2050 | €2010/GJ |
| `table11_dedicated_perennials.csv` | Table 11 | Cost of dedicated perennials (miscanthus, switchgrass, RCG), willow, poplar, 2020/2030/2050 | €2010/GJ |
| `table12_manure.csv` – `table15_secondary_forest_residues.csv` | Tables 12–15 | Costs of manure, agricultural and forest residues | €2010/GJ |
| `table20_biomass_emission_factors.csv` | Table 20 | Cultivation GHG emission factors per biomass type, 2010(2020)/2030/2050 | kgCO2eq/GJ |
| `table26_heating_values.csv` | Table 26 (Annex 5) | Mean lower heating value per feedstock (indexed by feedstock) | GJ/t |

Table 20 covers cultivation only (MITERRA-Europe: soil N2O, soil CO2 and organic soils, fertiliser
production, mechanisation; report p. 67). It excludes indirect land-use change and processing.
`0.0` in Table 20 means the crop is not produced in that country, not zero emissions.

## ENSPRESO database costs

`data/biomass_inputs/ENSPRESO_BIOMASS.xlsx`: JRC ENSPRESO biomass database (2019 version, as archived by
PyPSA-Eur), licensed CC BY 4.0. Source: https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/ENSPRESO/ENSPRESO_BIOMASS.xlsx.
`scripts/biomass_inputs/fill_country_tables.py` extracts sheet `COST - NUTS0 EnergyCom`, scenario `ENS_BaU_GFTM`
(the scenario used by technology-data for crop and fuelwood prices) for cereals, sugar beet, miscanthus/
switchgrass/RCG, willow, poplar, rape seed and fuelwood: `enspreso_costs_nuts0_ENS_BaU_GFTM.csv` (€2010/GJ).
Costs are in 2010 euros and need inflation adjustment before use.

## Complete per-country tables (filled)

The tables have gaps where a crop is not grown in a country, but PyPSA-Eur needs a value for every country
with unsustainable biomass (e.g. Italy and Portugal have large solid biofuel production but no willow value).
`fill_country_tables.py` therefore writes `*_filled.csv` versions of Tables 10, 11, 20 and the ENSPRESO costs:

1. A value is missing when it is empty or `0`.
2. Missing values get the mean of the land neighbours with a value (shared border within 5 km, from the NUTS
   2021 shapes; Bosnia and Herzegovina and Kosovo, not in NUTS, have their neighbours listed in the script).
   This is repeated, so countries surrounded by gaps are filled from the previous round.
3. Countries still missing (islands, or groups such as GB and IE that all lack the value) get the mean of the
   2 nearest countries with a value (centroid distance).

Country codes in the `*_filled.csv` files follow PyPSA-Eur (GB, GR, BA; Kosovo added as XK).
`filled_values_log.csv` lists every filled value with its method and donor countries.

## Upstream emissions and price of unsustainable biomass (used by PyPSA-Eur)

`compute_unsustainable_biomass_upstream.py` writes `outputs/biomass_inputs/unsustainable_biomass_upstream.csv`:
one row per country (PyPSA-Eur codes), columns `<quantity>_<year>`, ready to use in PyPSA-Eur's
unsustainable biomass (Eurostat primary production phased out by 2040).

Only the cultivation emissions that PyPSA-Eur does not already model are counted:

| Part | Counted | Why |
|---|---|---|
| Field N2O (direct and indirect) | yes | not modelled in PyPSA-Eur |
| N fertiliser production | imported share only (30%) | PyPSA-Eur models the ammonia produced in Europe |
| Farm diesel | no | PyPSA-Eur models the agriculture energy demand |
| P2O5, K2O, lime, pesticides | no | small (about 2 gCO2eq/MJ crop) |

This applies to the 1G crops, which are grown today, so their fertiliser and diesel are in the historical demand
of PyPSA-Eur. Willow (unsustainable solid biomass) is hardly grown today and keeps its full cultivation emissions.

| Quantity | Unit | Calculation | Value |
|---|---|---|---|
| `bioethanol` | tCO2eq/MWh fuel | wheat: (field N2O + 0.30 × N fertiliser) × crop per fuel × crop share 0.86 | 0.086 |
| `biodiesel` | tCO2eq/MWh fuel | rapeseed: (field N2O + 0.30 × N fertiliser) × crop per fuel × crop share 0.552 | 0.062 |
| `solid biomass` | tCO2eq/MWh | Table 20 willow (short rotation coppice), full cultivation emissions, per country | median 0.066 |
| `solid biomass price` | €2025/MWh | one EU willow value (see below), not used by PyPSA-Eur | |

Bioethanol and biodiesel are EU averages, repeated for every country and year (the layout read by PyPSA-Eur).

- **Cultivation inputs** per MJ of crop, EU averages of the JRC input data for the RED default values (Edwards et
  al. 2019, Tables 87 wheat, 131 sugar beet, 148 rapeseed): field N2O 0.0444, 0.01257 and 0.0572 g N2O/MJ
  (GWP 298); N fertiliser 0.0013, 0.00035 and 0.00184 kg N/MJ at 4,571.9 gCO2eq/kg N (Table 47).
- **Imported N fertiliser**: 30% of the EU nitrogen fertiliser is imported (European Commission 2022).
- **Crop per fuel**: tonne of fuel per tonne of crop from JRC Technical Report doi:10.2760/69179 (wheat 0.295 t/t at
  13.5% moisture, rapeseed 0.4176 t/t at 9%), JRC crop heating values (wheat 17.0, rapeseed 27.0 MJ/kg dry), fuel
  heating values ethanol 26.81 and biodiesel 36.7 GJ/t. All cultivation emissions are allocated to the fuel (none
  to co-products), so the values are an upper bound.
- **`cultivation_emissions_1G.csv`**: the same emissions per MWh of crop for cereals, sugar beet and rapeseed, field
  N2O and imported N fertiliser in separate columns, and the N fertiliser produced in Europe (70% of the use) in
  kg N per MWh of crop, on the heating value basis of the ENSPRESO 1G potentials (Table 26; sugar beet per tonne of
  dry matter, 25% dry matter as in JRC Table 131).

References: Edwards, R. et al. (2019), *Definition of input data to assess GHG default emissions from biofuels in
EU legislation*, version 1d, JRC, EUR 28349 EN, doi:10.2760/69179. European Commission (2022), *Ensuring
availability and affordability of fertilisers*, COM(2022) 590.
- **Crop share**: fuel from waste and residues has no cultivation emissions. Bioethanol: crops are 86% of EU ethanol
  feedstock, 2020–2022 (European Commission DG AGRI, *EU agricultural outlook 2023–2035*, p. 32). Biodiesel (incl.
  HVO, bio jet and other liquid biofuels): Eurostat SHARES 2024 (v2024.120925), sheet TRANSPORT, EU27 in 2021:
  (food and feed crop biofuels 10,097.9 ktoe − 0.86 × biogasoline 3,031.6 ktoe) / biodiesels 13,570.6 ktoe = 0.552.
- **Willow price**: mean of the countries with a non-zero cost in the ENSPRESO database (`ENS_BaU_GFTM`, the method
  technology-data uses for its ENSPRESO prices), converted from €2010/GJ to €2025/MWh with the Eurostat HICP
  (`data/biomass_inputs/eurostat_prc_hicp_aind.xlsx`, EEA, factor 1.444 as in technology-data; Eurostat dataset
  [prc_hicp_aind](https://ec.europa.eu/eurostat/databrowser/view/prc_hicp_aind/default/table), data as of
  6 February 2026). A single EU value, so it is the same with or without spatially resolved
  biomass.

**Inflation factor 2010 → 2025 (1.444).** ENSPRESO costs are in €2010. They are converted to €2025 with the
annual rate of change of the Harmonised Index of Consumer Prices (HICP) for the European Economic Area (Eurostat
`prc_hicp_aind`, extracted 13 February 2026, data as of 6 February 2026, file
`data/biomass_inputs/eurostat_prc_hicp_aind.xlsx`), compounded over 2011–2025:

factor = (1 + r₂₀₁₁) × (1 + r₂₀₁₂) × … × (1 + r₂₀₂₅) = 1.44426

| Year | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| r (%) | 3.1 | 2.6 | 1.5 | 0.6 | 0.1 | 0.3 | 1.7 | 1.9 | 1.5 | 0.7 | 2.9 | 9.2 | 6.4 | 2.6 | 2.5 |

This is the method of technology-data (`adjust_for_inflation` in `scripts/_helpers.py`: same Eurostat dataset
and EEA row, cumulative product from the year after the currency year to the target year; a missing year would
take the mean rate, but no year is missing here). It is computed in `inflation_factor()` of
`scripts/biomass_inputs/compute_unsustainable_biomass_upstream.py`.

---

# PyPSA-Eur output files summary

The following files from this package are directly read by the PyPSA-Eur workflow

| File | Technology | Description |
|------|------------|-------------|
| `outputs/afforestation/afforestation_nuts_biomass_densities.xlsx` | Afforestation | Biomass density per NUTS-2 (`"density"` method) |
| `outputs/afforestation/afforestation_rates_nuts2_full.csv` | Afforestation | Rotation-averaged MAI per NUTS-2 (`"growth"` method) |
| `outputs/afforestation/afforestation_nuts2_monthly_weights.csv` | Afforestation | Monthly GPP weights for seasonal dispatch profile |
| `outputs/perennialisation/eurostat_apro_cpshr_nuts2_raw.csv` | Perennialisation | Eurostat crop harvest at NUTS-2 |
| `outputs/perennialisation/eurostat_apro_cpshr_nuts0_raw.csv` | Perennialisation | Eurostat crop harvest at NUTS-0 |
| `outputs/biomass_inputs/unsustainable_biomass_upstream.csv` | Unsustainable biomass | Upstream emission factors per country and EU willow price |
| `outputs/biomass_inputs/cultivation_emissions_1G.csv` | Unsustainable biomass and perennialisation | Cultivation emissions of the 1G crops per MWh of crop |

---

## Licence

Copyright 2026 Alberto Alamia and Contributors to PyPSA-Eur

The code in `scripts/` is released as free software under the MIT licence, see
[LICENSE](LICENSE). However, different licenses and terms of use may apply to the various
input data — see the per-dataset "Raw input" sections above for each dataset's own reference
and access terms (Eurostat, Pilli et al./JRC, Avitabile et al./Figshare, FluxCom/Jung et al.,
Ruiz et al./JRC ENSPRESO).

---

## Reproducibility note

Re-running the download scripts in the future may produce different results if the
upstream APIs, dataset coverage, labels, or definitions change. The archived files
in this package should therefore be treated as the fixed reference inputs for this
version of the workflow.
