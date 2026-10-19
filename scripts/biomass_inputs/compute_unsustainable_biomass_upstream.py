#!/usr/bin/env python3
# SPDX-FileCopyrightText: Contributors to PyPSA-Eur <https://github.com/pypsa/pypsa-eur>
# SPDX-License-Identifier: MIT

"""
Upstream (feedstock cultivation) emission factors and the price of the
unsustainable biomass in PyPSA-Eur, ready to use: one table, one row per
country, columns "<quantity>_<year>"; plus a per-crop table of the cultivation
emissions of 1st-generation (1G) biofuel crops.

Only the emissions that PyPSA-Eur does not already model are counted:
- field N2O (direct and indirect) of the crop: always counted;
- production of the N fertiliser: counted only for the imported share
  (PyPSA-Eur models the ammonia produced in Europe);
- farm diesel: not counted (PyPSA-Eur models the agriculture energy demand);
- P2O5, K2O, lime and pesticides: not counted (small).

Quantities
----------
bioethanol, biodiesel : tCO2eq per MWh of fuel
    EF = (N2O_field + s_import * N_fert * EF_N) * E_crop / (eff * LHV_fuel) * crop_share
    - N2O_field (gN2O/MJ crop, GWP 298) and N_fert (kg N/MJ crop): EU averages
      of the JRC input data for the RED default values (Edwards et al. 2019,
      Tables 87 wheat, 131 sugar beet, 148 rapeseed); EF_N = 4571.9 gCO2eq/kg N
      (Table 47).
    - s_import = 0.30: share of the EU nitrogen fertiliser that is imported
      (European Commission 2022, COM(2022) 590).
    - E_crop: MJ per tonne of crop at the traded moisture (JRC LHV and water
      content), eff: tonne of fuel per tonne of crop (JRC, doi:10.2760/69179),
      LHV_fuel: heating value of the fuel. Bioethanol uses wheat.
    - crop_share: share of the fuel made from crops; fuel from waste and
      residues has no cultivation emissions.
solid biomass : tCO2eq per MWh
    ENSPRESO Table 20 willow (short rotation coppice), full cultivation
    emissions: willow is hardly grown today, so its fertiliser and diesel are
    not in the historical demand that PyPSA-Eur models.
solid biomass price : EUR2025 per MWh
    Single EU value for willow: mean of the countries with a non-zero cost in the
    JRC ENSPRESO biomass database, scenario ENS_BaU_GFTM (the method
    technology-data uses for its ENSPRESO prices), inflated from 2010 to 2025
    with the Eurostat HICP as in technology-data. Not used by PyPSA-Eur.

Bioethanol and biodiesel are EU averages, repeated for every country and year,
so the table keeps the layout read by PyPSA-Eur. Countries use PyPSA-Eur codes.

cultivation_emissions_1G.csv : kgCO2eq per MWh of crop, per crop
    field N2O and imported N fertiliser separately, and the N fertiliser
    produced in Europe (70% of the use, kg N per MWh of crop), on the heating value basis
    of the ENSPRESO 1G potentials (Ruiz et al. 2015, Table 26; sugar beet per
    tonne of dry matter, 25% dry matter as in JRC Table 131).
"""

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "outputs" / "biomass_inputs"
DATA = REPO / "data" / "biomass_inputs"

# --- cultivation inputs per MJ of crop (Edwards et al. 2019, JRC EUR 28349) -
GWP_N2O = 298
EF_N_FERTILISER = 4571.9  # gCO2eq/kg N, production (Table 47)
S_IMPORT_N = 0.30  # imported share of EU N fertiliser (COM(2022) 590)
CROPS = {
    # n2o: g N2O/MJ crop; n: kg N/MJ crop; mj_per_t: MJ per tonne at traded moisture
    "cereals": dict(n2o=0.0444, n=0.0013, mj_per_t=17.0 * (1 - 0.135) * 1e3, table26="Cereals", dry_matter=1.0),
    "sugar beet": dict(n2o=0.01257, n=0.00035, mj_per_t=16.3 * 0.25 * 1e3, table26="Sugar Beet", dry_matter=0.25),
    "rapeseed": dict(n2o=0.0572, n=0.00184, mj_per_t=27.0 * (1 - 0.09) * 1e3, table26="Rape", dry_matter=1.0),
}

# --- crop-to-fuel conversion (JRC Technical Report doi:10.2760/69179) --------
# tonne of fuel per tonne of crop at the traded moisture (wheat 13.5%, rapeseed 9%)
CONVERSION = {
    "bioethanol": dict(crop="cereals", efficiency=0.295, lhv_fuel=26.81),  # GJ/t ethanol
    "biodiesel": dict(crop="rapeseed", efficiency=0.4176, lhv_fuel=36.7),  # GJ/t biodiesel
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


def cultivation_per_mj(crop: dict) -> tuple[float, float]:
    """Field N2O and imported N fertiliser production, gCO2eq per MJ of crop."""
    return crop["n2o"] * GWP_N2O, S_IMPORT_N * crop["n"] * EF_N_FERTILISER


def main() -> None:
    table20 = pd.read_csv(OUT / "table20_biomass_emission_factors_filled.csv", index_col=0)
    countries = table20.index
    table26 = pd.read_csv(OUT / "table26_heating_values.csv", index_col=0).squeeze("columns")
    years = [2010, 2030, 2050]

    result = {}
    for fuel, c in CONVERSION.items():
        crop = CROPS[c["crop"]]
        g_per_mj_crop = sum(cultivation_per_mj(crop))
        mj_crop_per_mj_fuel = crop["mj_per_t"] / (c["efficiency"] * c["lhv_fuel"] * 1e3)
        ef = g_per_mj_crop * mj_crop_per_mj_fuel * CROP_SHARE[fuel] * GJ_PER_MWH / 1e3  # t/MWh
        for year in years:
            result[f"{fuel}_{year}"] = ef
        print(f"{fuel}: {g_per_mj_crop:.2f} gCO2eq/MJ crop, {mj_crop_per_mj_fuel:.4f} MJ crop/MJ fuel, crop share {CROP_SHARE[fuel]:.4f}, {ef:.4f} t/MWh")

    for year, values in year_columns(table20, "Willow").items():
        result[f"solid biomass_{year}"] = values * GJ_PER_MWH / 1e3

    costs = pd.read_csv(OUT / "enspreso_costs_nuts0_ENS_BaU_GFTM.csv", index_col=0)
    willow = year_columns(costs, "Willow")
    factor = inflation_factor(2010, EUR_YEAR)
    price = willow.where(willow > 0).mean() * GJ_PER_MWH * factor
    for year, value in price.items():
        result[f"solid biomass price_{year}"] = value

    table = pd.DataFrame(result, index=countries)
    table.index.name = "country"
    table.round(6).to_csv(OUT / "unsustainable_biomass_upstream.csv")
    print(f"Wrote unsustainable_biomass_upstream.csv ({table.shape[0]} countries x {table.shape[1]} columns)")

    rows = {}
    for name, crop in CROPS.items():
        field, fert = cultivation_per_mj(crop)
        # MJ (JRC basis) per MWh of crop on the ENSPRESO Table 26 basis
        mj_per_mwh = crop["mj_per_t"] / (table26[crop["table26"]] * crop["dry_matter"] / GJ_PER_MWH)
        rows[name] = {
            "field N2O [kgCO2eq/MWh crop]": field * mj_per_mwh / 1e3,
            "imported N fertiliser [kgCO2eq/MWh crop]": fert * mj_per_mwh / 1e3,
            "EU-produced N fertiliser [kgN/MWh crop]": (1 - S_IMPORT_N) * crop["n"] * mj_per_mwh,
        }
    crops = pd.DataFrame(rows).T
    crops.insert(2, "total [kgCO2eq/MWh crop]", crops.iloc[:, :2].sum(axis=1))
    crops.index.name = "crop"
    crops.round(4).to_csv(OUT / "cultivation_emissions_1G.csv")
    print(crops.round(2))


if __name__ == "__main__":
    main()
