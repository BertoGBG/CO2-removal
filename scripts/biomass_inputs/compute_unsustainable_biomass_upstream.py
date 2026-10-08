#!/usr/bin/env python3
# SPDX-FileCopyrightText: Contributors to PyPSA-Eur <https://github.com/pypsa/pypsa-eur>
# SPDX-License-Identifier: MIT

"""
Per-country upstream (feedstock cultivation) emission factors and the price of
the unsustainable biomass in PyPSA-Eur, ready to use: one table, one row per
country, columns "<quantity>_<year>".

Quantities
----------
bioethanol, biodiesel : tCO2eq per MWh of fuel
    EF = EF_T20 * feedstock_input * crop_share * 3.6 / 1000
    - EF_T20: JRC ENSPRESO Table 20 (Ruiz et al. 2015) cultivation emissions,
      kgCO2eq/GJ of feedstock, starchy crops (bioethanol) and rapeseed
      (biodiesel), missing countries filled from neighbours
      (fill_country_tables.py).
    - feedstock_input: GJ of feedstock per GJ of fuel on the heating value basis
      of the report, LHV_T26 / (efficiency * LHV_fuel). All cultivation emissions
      are allocated to the fuel (none to co-products).
    - crop_share: share of the fuel made from crops; fuel from waste and
      residues has no cultivation emissions.
solid biomass : tCO2eq per MWh
    Table 20 willow (short rotation coppice), no conversion.
solid biomass price : EUR2025 per MWh
    Single EU value for willow: mean of the countries with a non-zero cost in the
    JRC ENSPRESO biomass database, scenario ENS_BaU_GFTM (the method
    technology-data uses for its ENSPRESO prices), inflated from 2010 to 2025
    with the Eurostat HICP as in technology-data. Repeated in every row, so it
    does not depend on spatial resolution.

Countries use PyPSA-Eur codes (GB, GR, BA; XK added).
"""

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "outputs" / "biomass_inputs"
DATA = REPO / "data" / "biomass_inputs"

# --- crop-to-fuel conversion (JRC Technical Report doi:10.2760/69179) --------
# mass efficiencies at the moisture of the Eurostat production statistics:
# wheat 0.295 t/t at 13.5% moisture -> 14% Eurostat standard humidity;
# rapeseed 0.4176 t/t at 9% moisture (= Eurostat standard)
CONVERSION = {
    "bioethanol": dict(
        table20="Starchy_crops_barley_wheat_maize_oats_rye",
        table26="Cereals",
        efficiency=0.295 * (1 - 0.14) / (1 - 0.135),
        lhv_fuel=26.81,  # GJ/t ethanol
    ),
    "biodiesel": dict(
        table20="Rapeseed_biodiesel",
        table26="Rape",
        efficiency=0.4176,
        lhv_fuel=36.7,  # GJ/t biodiesel
    ),
}

# --- crop-based shares -------------------------------------------------------
# bioethanol: crops (cereals, sugar beet, molasses) in EU ethanol feedstock,
# 2020-2022, by ethanol volume (DG AGRI, EU agricultural outlook 2023-2035, p. 32)
SHARE_CROP_ETHANOL = 0.86
# biodiesel: Eurostat SHARES 2024 (v2024.120925), sheet TRANSPORT, EU27, 2021, ktoe
SHARES_FOOD_FEED_CROPS = 10097.9  # Article 26(1), biogasoline and biodiesels
SHARES_BIOGASOLINE = 3031.6
SHARES_BIODIESELS = 13570.6  # biodiesels + bio jet kerosene + other liquid biofuels
CROP_SHARE = {
    "bioethanol": SHARE_CROP_ETHANOL,
    "biodiesel": (SHARES_FOOD_FEED_CROPS - SHARE_CROP_ETHANOL * SHARES_BIOGASOLINE)
    / SHARES_BIODIESELS,
}

GJ_PER_MWH = 3.6
EUR_YEAR = 2025
HICP_ROW = "European Economic Area (EEA18-1995, EEA28-2004, EEA30-2007, EEA31-2013, EEA30-2020)"


def inflation_factor(from_year: int, to_year: int) -> float:
    """Cumulative Eurostat HICP inflation, as technology-data's adjust_for_inflation."""
    rate = (
        pd.read_excel(
            DATA / "eurostat_prc_hicp_aind.xlsx",
            sheet_name="Sheet 1",
            index_col=0,
            na_values=[":", "d"],
            header=8,
        )
        .loc[HICP_ROW]
        .dropna()
    )
    rate.index = rate.index.astype(int)
    rate = rate.astype(float) / 100
    years = np.arange(from_year + 1, to_year + 1)
    return float((1 + rate.reindex(years).fillna(rate.mean())).prod())


def year_columns(table: pd.DataFrame, prefix: str) -> pd.DataFrame:
    columns = table.filter(regex=rf"^{prefix}_\d{{4}}$")
    return columns.rename(columns=lambda c: int(c[-4:]))


def main() -> None:
    table20 = pd.read_csv(OUT / "table20_biomass_emission_factors_filled.csv", index_col=0)
    table26 = pd.read_csv(OUT / "table26_heating_values.csv", index_col=0).squeeze("columns")

    result = {}
    for fuel, c in CONVERSION.items():
        feedstock_input = table26[c["table26"]] / (c["efficiency"] * c["lhv_fuel"])
        ef = year_columns(table20, c["table20"]) * feedstock_input * CROP_SHARE[fuel]
        for year, values in ef.items():
            result[f"{fuel}_{year}"] = values * GJ_PER_MWH / 1e3
        print(f"{fuel}: feedstock input {feedstock_input:.4f}, crop share {CROP_SHARE[fuel]:.4f}")

    for year, values in year_columns(table20, "Willow").items():
        result[f"solid biomass_{year}"] = values * GJ_PER_MWH / 1e3

    costs = pd.read_csv(OUT / "enspreso_costs_nuts0_ENS_BaU_GFTM.csv", index_col=0)
    willow = year_columns(costs, "Willow")
    factor = inflation_factor(2010, EUR_YEAR)
    price = willow.where(willow > 0).mean() * GJ_PER_MWH * factor
    for year, value in price.items():
        result[f"solid biomass price_{year}"] = value
    print(f"willow price EUR{EUR_YEAR}/MWh (factor {factor:.5f}): {price.round(2).to_dict()}")

    table = pd.DataFrame(result, index=table20.index)
    table.index.name = "country"
    table.round(6).to_csv(OUT / "unsustainable_biomass_upstream.csv")
    print(f"Wrote unsustainable_biomass_upstream.csv ({table.shape[0]} countries x {table.shape[1]} columns)")


if __name__ == "__main__":
    main()
