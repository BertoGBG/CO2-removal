#!/usr/bin/env python3
# SPDX-FileCopyrightText: Contributors to PyPSA-Eur <https://github.com/pypsa/pypsa-eur>
# SPDX-License-Identifier: MIT

"""
Extract country-level cost/emission-factor tables from
"Biomass potentials in Europe" (EU JRC report) into one CSV per table.

Source PDF (relative to the repository root):
    data/biomass_inputs/Ruiz2015_JRC-EU-TIMES_bioenergy_potentials_EUR27575.pdf
    Ruiz et al. (2015), The JRC-EU-TIMES model. Bioenergy potentials for EU and
    neighbouring countries, EUR 27575 EN, doi:10.2790/39014.

Outputs (relative to the repository root):
    outputs/biomass_inputs/*.csv

Tables extracted (all indexed by NUTS0/country code):
    Table 10 - Cost of biofuel crops and energy maize, medium scenario (Euro2010/GJ)
    Table 11 - Cost of dedicated perennials, medium scenario (Euro2010/GJ)
    Table 12 - Cost of manure, medium scenario (Euro2010/GJ)
    Table 13 - Cost of primary agricultural residues, medium scenario (Euro2010/GJ)
    Table 14 - Cost of forest products and primary forest residues, medium scenario (Euro2010/GJ)
    Table 15 - Cost of secondary forest residues, medium scenario (Euro2010/GJ)
    Table 20 - Biomass emission factors, GHG (kg CO2eq/GJ)

Also extracted (indexed by feedstock):
    Table 26 - Heating values of main biomass feedstocks (GJ/t; the header
               reads "Mean LHV (TJ/ton) (GJ/ton)", values are GJ/t)

Approach:
    The PDF has no embedded table grid -- pdfplumber's extract_text() layout
    mode reproduces the whitespace-aligned columns as plain text, one country
    per text line (some pages print two countries side by side on one line).
    Every data line starts with a 2-letter country code from a fixed list
    used consistently throughout the report, followed by a fixed number of
    numeric fields ("-" = not available -> NaN) for that table. We scan the
    page text token by token and greedily match "<CODE> <N numbers>" -- this
    is robust to the single-column vs. two-country-per-line layouts without
    needing to special-case each page.

Usage:
    python scripts/extract_enspreso_tables.py [--pdf PATH] [--out-dir DIR]

Requires: pdfplumber (pip install pdfplumber)
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd
import pdfplumber

# Country/NUTS0 codes used throughout the report (36 countries, EU28 + Balkans/EFTA).
COUNTRY_CODES = [
    "AL", "AT", "BE", "BG", "BH", "CH", "CY", "CZ", "DE", "DK",
    "EE", "ES", "FI", "FR", "GR", "HR", "HU", "IE", "IS", "IT",
    "LT", "LU", "LV", "ME", "MK", "MT", "NL", "NO", "PL", "PT",
    "RO", "RS", "SE", "SI", "SK", "UK",
]

NUMERIC_RE = re.compile(r"^-?\d+(\.\d+)?$")


def _parse_value(token: str) -> float | None:
    if token == "-":
        return None
    if NUMERIC_RE.match(token):
        return float(token)
    return None


def _is_data_token(token: str) -> bool:
    return token == "-" or bool(NUMERIC_RE.match(token))


def extract_country_table(pages_text: str, n_values: int) -> dict[str, list[float | None]]:
    """Scan whitespace-tokenised page text for '<CODE> v1 v2 ... vN' runs.

    Works for both single-country-per-line pages and two-countries-per-line
    (side-by-side) pages, since it only looks at token sequences, not lines.
    """
    tokens = pages_text.split()
    rows: dict[str, list[float | None]] = {}
    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        if tok in COUNTRY_CODES:
            candidate = tokens[i + 1 : i + 1 + n_values]
            if len(candidate) == n_values and all(_is_data_token(t) for t in candidate):
                rows[tok] = [_parse_value(t) for t in candidate]
                i += 1 + n_values
                continue
        i += 1
    return rows


def build_columns(categories: list[str], years_per_category: list[list[int]]) -> list[str]:
    cols = []
    for cat, years in zip(categories, years_per_category):
        for y in years:
            cols.append(f"{cat}_{y}")
    return cols


def pages_range_text(pdf: pdfplumber.PDF, page_indices: list[int]) -> str:
    return "\n".join(pdf.pages[i].extract_text() or "" for i in page_indices)


def make_dataframe(rows: dict[str, list[float | None]], columns: list[str]) -> pd.DataFrame:
    df = pd.DataFrame.from_dict(rows, orient="index", columns=columns)
    df.index.name = "country"
    df = df.sort_index()
    n_expected = len(COUNTRY_CODES)
    if len(df) != n_expected:
        missing = sorted(set(COUNTRY_CODES) - set(df.index))
        print(f"  [warning] expected {n_expected} countries, got {len(df)}. Missing: {missing}")
    return df


TABLE_SPECS = [
    dict(
        name="table10_biofuel_crops",
        pages=[50, 51],  # 0-indexed pdf pages (printed pages 49-50)
        categories=["Sugar_beet", "Oil_crops_rapeseed_sunflower_soya", "Starchy_crops_barley_wheat_maize_oats_rye"],
        years=[[2010, 2030, 2050]] * 3,
    ),
    dict(
        name="table11_dedicated_perennials",
        pages=[52, 53],
        categories=["Dedicated_perennials_miscanthus_switchgrass_RCG", "Willow", "Poplar"],
        years=[[2020, 2030, 2050]] * 3,
    ),
    dict(
        name="table12_manure",
        pages=[54],
        categories=["Liquid_and_solid_manure"],
        years=[[2010, 2030, 2050]],
    ),
    dict(
        name="table13_primary_agri_residues",
        pages=[56],
        categories=["Primary_agricultural_residues"],
        years=[[2010, 2030, 2050]],
    ),
    dict(
        name="table14_forest_products_primary_residues",
        pages=[57, 58],
        categories=["Roundwood_fuelwood", "Roundwood_chips_and_pellets", "Forest_residues_chips_pellets"],
        years=[[2010, 2030, 2050]] * 3,
    ),
    dict(
        name="table15_secondary_forest_residues",
        pages=[59, 60],
        categories=["Secondary_forestry_residues_woodchips", "Secondary_forestry_residues_sawdust"],
        years=[[2010, 2030, 2050]] * 2,
    ),
    dict(
        name="table20_biomass_emission_factors",
        pages=[69, 70, 71],
        categories=[
            "Sugarbeet_bioethanol",
            "Oil_crops_other_than_rapeseed_sunflower_soya",
            "Rapeseed_biodiesel",
            "Starchy_crops_barley_wheat_maize_oats_rye",
            "Dedicated_perennials_miscanthus_switchgrass_RCG",
            "Willow",
        ],
        years=[[2010, 2030, 2050]] * 4 + [[2020, 2030, 2050]] * 2,
    ),
]


HEATING_VALUES_PAGE = 95  # 0-indexed pdf page of Table 26 (Annex 5, printed page 94)


def extract_heating_values(page_text: str) -> pd.DataFrame:
    """
    Parse Table 26 (heating values of main biomass feedstocks).

    The table prints two "<feedstock> <value>" columns side by side. Lines
    without a decimal value continue the name of the last feedstock whose
    parenthesis is still open (the wrapped "Wet manure (corrected ..." entry).
    The report lists a few feedstocks in both columns; exact duplicates
    (case-insensitive name, same value) are dropped.
    """
    lines = page_text.splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("Mean LHV")) + 1

    entries: list[list] = []
    for line in lines[start:]:
        if re.match(r"^\d+\s*\|", line):  # page footer, e.g. "94 | Pa ge"
            continue
        pairs = re.findall(r"(.+?)\s+(\d+\.\d+)(?=\s|$)", line)
        if pairs:
            entries.extend([name.strip(), float(value)] for name, value in pairs)
        else:
            open_entry = next(
                (e for e in reversed(entries) if e[0].count("(") > e[0].count(")")),
                None,
            )
            if open_entry is not None:
                open_entry[0] = f"{open_entry[0]} {line.strip()}"

    df = pd.DataFrame(entries, columns=["feedstock", "LHV_GJ_per_t"])
    df = df.loc[~df.assign(key=df.feedstock.str.lower()).duplicated(["key", "LHV_GJ_per_t"])]
    return df.set_index("feedstock")


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    default_pdf = (
        repo_root
        / "data"
        / "biomass_inputs"
        / "Ruiz2015_JRC-EU-TIMES_bioenergy_potentials_EUR27575.pdf"
    )
    default_out = repo_root / "outputs" / "biomass_inputs"

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=default_pdf, help="Path to the source PDF")
    parser.add_argument("--out-dir", type=Path, default=default_out, help="Directory to write CSVs into")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)

    with pdfplumber.open(args.pdf) as pdf:
        for spec in TABLE_SPECS:
            n_values = sum(len(y) for y in spec["years"])
            text = pages_range_text(pdf, spec["pages"])
            rows = extract_country_table(text, n_values)
            columns = build_columns(spec["categories"], spec["years"])
            df = make_dataframe(rows, columns)

            out_path = args.out_dir / f"{spec['name']}.csv"
            df.to_csv(out_path)
            print(f"Wrote {out_path} ({len(df)} countries x {len(columns)} value columns)")

        df = extract_heating_values(pdf.pages[HEATING_VALUES_PAGE].extract_text())
        out_path = args.out_dir / "table26_heating_values.csv"
        df.to_csv(out_path)
        print(f"Wrote {out_path} ({len(df)} feedstocks)")


if __name__ == "__main__":
    main()
