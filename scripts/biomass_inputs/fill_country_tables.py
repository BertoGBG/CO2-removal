#!/usr/bin/env python3
# SPDX-FileCopyrightText: Contributors to PyPSA-Eur <https://github.com/pypsa/pypsa-eur>
# SPDX-License-Identifier: MIT

"""
Build complete per-country biomass cost and emission-factor tables for PyPSA-Eur.

Inputs (relative to the repository root):
    outputs/biomass_inputs/table10_biofuel_crops.csv
    outputs/biomass_inputs/table11_dedicated_perennials.csv
    outputs/biomass_inputs/table20_biomass_emission_factors.csv
        extracted from Ruiz et al. (2015) by extract_enspreso_tables.py
    data/biomass_inputs/ENSPRESO_BIOMASS.xlsx
        JRC ENSPRESO biomass database (2019 version, CC BY 4.0), sheet
        "COST - NUTS0 EnergyCom", scenario ENS_BaU_GFTM
    data/nuts/NUTS_RG_01M_2021_4326_LEVL_2.geojson
        used to find neighbouring countries

Outputs (outputs/biomass_inputs/):
    enspreso_costs_nuts0_ENS_BaU_GFTM.csv     costs per country, Euro2010/GJ (as in the database)
    *_filled.csv                              the four tables with missing values filled
    filled_values_log.csv                     one row per filled value, with method and donors

Filling:
    A value is missing when it is empty or 0 (in Table 20, 0 means the crop is not
    produced in the country). Missing values are filled with the mean of the land
    neighbours that have a value; this is repeated so that countries surrounded by
    missing values are filled from the values filled in the previous round.
    Countries still missing after that (islands, or groups of neighbours that all
    lack the value, such as GB and IE) use the 2 nearest countries with a value
    (centroid distance). Anything still missing gets the mean of all original values.

Country codes in the outputs follow PyPSA-Eur (ISO 3166-1 alpha-2, with GB for the
United Kingdom and GR for Greece); ENSPRESO's UK and BH and NUTS' UK and EL are
converted. Kosovo (XK) is not in ENSPRESO and is filled from its neighbours.
"""

from pathlib import Path

import geopandas as gpd
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "outputs" / "biomass_inputs"
ENSPRESO_XLSX = REPO / "data" / "biomass_inputs" / "ENSPRESO_BIOMASS.xlsx"
NUTS = REPO / "data" / "nuts" / "NUTS_RG_01M_2021_4326_LEVL_2.geojson"

TO_PYPSA = {"UK": "GB", "BH": "BA", "EL": "GR"}

# Bosnia and Herzegovina and Kosovo are not in NUTS 2021: land borders added by hand
EXTRA_NEIGHBOURS = {"BA": ["HR", "RS", "ME"], "XK": ["RS", "ME", "AL", "MK"]}
EXTRA_COUNTRIES = ["XK"]

ENSPRESO_COMMODITIES = {
    "MINBIOCRP11": "Bioethanol_barley_wheat_grain_maize_oats_other_cereals_rye",
    "MINBIOCRP21": "Sugar_from_sugar_beet",
    "MINBIOCRP31": "Miscanthus_switchgrass_RCG",
    "MINBIOCRP41": "Willow",
    "MINBIOCRP41a": "Poplar",
    "MINBIORPS1": "Rape_seed",
    "MINBIOWOO": "FuelwoodRW",
}

N_NEAREST = 2


def neighbours() -> tuple[dict[str, list[str]], pd.Series]:
    """Land neighbours (shared border within 5 km) and country centroids."""
    shapes = gpd.read_file(NUTS).dissolve("CNTR_CODE")[["geometry"]].to_crs(3035)
    shapes.index = shapes.index.map(lambda c: TO_PYPSA.get(c, c))
    buffered = shapes.buffer(5000)
    nb = {
        c: [o for o in shapes.index if o != c and buffered[c].intersects(shapes.geometry[o])]
        for c in shapes.index
    }
    for c, others in EXTRA_NEIGHBOURS.items():
        nb[c] = list(others)
        for o in others:
            nb.setdefault(o, [])
            if c not in nb[o]:
                nb[o].append(c)
    centroids = shapes.centroid
    return nb, centroids


def enspreso_costs() -> pd.DataFrame:
    """Per-country costs of the ENS_BaU_GFTM scenario, Euro2010/GJ, wide format."""
    df = pd.read_excel(ENSPRESO_XLSX, sheet_name="COST - NUTS0 EnergyCom")
    df.columns = [c.strip() for c in df.columns]
    df = df[(df["Scenario"] == "ENS_BaU_GFTM") & df["Energy Commodity"].isin(ENSPRESO_COMMODITIES)]
    df["value"] = pd.to_numeric(df["NUTS0 Energy Commodity Cost"], errors="coerce")
    df["column"] = df["Energy Commodity"].map(ENSPRESO_COMMODITIES) + "_" + df["Year"].astype(str)
    wide = df.pivot_table(index="NUTS0", columns="column", values="value", aggfunc="first")
    wide.index.name = "country"
    return wide[sorted(wide.columns)]


def fill(table: pd.DataFrame, name: str, nb: dict, centroids: pd.Series) -> tuple[pd.DataFrame, list]:
    countries = sorted(set(table.index) | set(EXTRA_COUNTRIES))
    table = table.reindex(countries)
    original = table.where(table.notna() & (table != 0))
    filled = original.copy()
    log = []
    for col in table.columns:
        known = original[col].dropna()
        if known.empty:
            continue
        rnd = 0
        while True:
            rnd += 1
            current = filled[col]
            missing = current.index[current.isna()]
            updates = {}
            for c in missing:
                donors = [o for o in nb.get(c, []) if o in current.index and pd.notna(current[o])]
                if donors:
                    updates[c] = (current[donors].mean(), f"neighbours (round {rnd})", donors)
            if not updates:
                break
            for c, (v, method, donors) in updates.items():
                filled.loc[c, col] = v
                log.append((name, col, c, round(v, 4), method, " ".join(donors)))
        for c in filled.index[filled[col].isna()]:
            if c in centroids.index:
                cand = filled[col].dropna()
                cand = cand[cand.index.isin(centroids.index)]
                dist = centroids[cand.index].distance(centroids[c]).sort_values()
                donors = list(dist.index[:N_NEAREST])
                v, method = cand[donors].mean(), f"{N_NEAREST} nearest countries"
            else:
                donors, v, method = [], known.mean(), "mean of all original values"
            filled.loc[c, col] = v
            log.append((name, col, c, round(v, 4), method, " ".join(donors)))
    return filled, log


def main() -> None:
    nb, centroids = neighbours()

    costs = enspreso_costs()
    costs.to_csv(OUT / "enspreso_costs_nuts0_ENS_BaU_GFTM.csv")
    print(f"Wrote enspreso_costs_nuts0_ENS_BaU_GFTM.csv ({costs.shape[0]} countries)")

    tables = {
        "table10_biofuel_crops": pd.read_csv(OUT / "table10_biofuel_crops.csv", index_col=0),
        "table11_dedicated_perennials": pd.read_csv(OUT / "table11_dedicated_perennials.csv", index_col=0),
        "table20_biomass_emission_factors": pd.read_csv(OUT / "table20_biomass_emission_factors.csv", index_col=0),
        "enspreso_costs_nuts0_ENS_BaU_GFTM": costs,
    }
    log = []
    for name, table in tables.items():
        table = table.rename(index=lambda c: TO_PYPSA.get(c, c))
        filled, entries = fill(table, name, nb, centroids)
        filled.round(4).to_csv(OUT / f"{name}_filled.csv")
        log += entries
        print(f"Wrote {name}_filled.csv ({len(entries)} values filled)")

    pd.DataFrame(log, columns=["table", "column", "country", "value", "method", "donors"]).to_csv(
        OUT / "filled_values_log.csv", index=False
    )


if __name__ == "__main__":
    main()
