#!/usr/bin/env python3
"""One-off: find municipalities above a population threshold that aren't in
providers.csv at all (no known open data portal, so never added).

Review-only — writes a candidate CSV, does NOT touch providers.csv. Compares
the full StatCan CSD list (all 5,161 municipalities) against providers.csv's
existing dguid values; anything above the threshold and not already covered
is a candidate worth a look before deciding whether/how to add it (with a
blank portal_url, to be periodically re-checked like any other provider).

Excludes CSDTYPE codes that aren't real municipal governments (Indian
reserves, unorganized territory) — everything else is left for you to judge,
CSDTYPE is included in the output.

Usage:
    python find_missing_municipalities.py [--min-population 15000]
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd


def normalize(name: str) -> str:
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = name.lower().replace("&", " and ").replace(".", " ").replace("-", " ")
    name = re.sub(r"\s+", " ", name).strip()
    return name


REPO_ROOT = Path(__file__).resolve().parent.parent
CSD_PARQUET = REPO_ROOT / "data/reference/statcan_csd_2021.parquet"
POPULATION_PARQUET = REPO_ROOT / "data/reference/statcan_population_2021.parquet"
PROVIDERS_CSV = REPO_ROOT / "ca-data-providers/providers.csv"
POPULATION_COLUMN = "Population and dwelling counts (5): Population, 2021 [1]"
OUTPUT_CSV = Path(__file__).parent / "missing_municipalities_candidates.csv"

# Not real municipal governments -- Indian reserves, unorganized territory.
EXCLUDE_CSDTYPES = {"IRI", "NO", "SNO"}

PRUID_PROVINCE = {
    "10": "NL", "11": "PE", "12": "NS", "13": "NB", "24": "QC", "35": "ON",
    "46": "MB", "47": "SK", "48": "AB", "59": "BC", "60": "YT", "61": "NT", "62": "NU",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--min-population", type=int, default=15000)
    args = parser.parse_args()

    csd = pd.read_parquet(CSD_PARQUET, columns=["DGUID", "CSDNAME", "CSDTYPE", "PRUID"])
    pop = pd.read_parquet(POPULATION_PARQUET, columns=["DGUID", POPULATION_COLUMN])
    providers = pd.read_csv(PROVIDERS_CSV, dtype=str).fillna("")

    existing_dguids = set(providers["dguid"]) - {""}
    # Belt-and-suspenders vs. dguid: some existing providers (e.g. Halifax Regional
    # Municipality) got miscategorized upstream as region/other and never got a
    # dguid filled in, even though they're a real, already-tracked CSD. Catch those
    # by name too, so they don't reappear here as false "missing" candidates.
    providers["norm_name"] = providers["name"].apply(normalize)
    providers_by_province = providers.groupby("province")["norm_name"].apply(list).to_dict()

    def already_tracked_by_name(csd_name_norm: str, province: str) -> bool:
        return any(
            csd_name_norm in prov_name or prov_name in csd_name_norm
            for prov_name in providers_by_province.get(province, [])
        )

    merged = csd.merge(pop, on="DGUID", how="left")
    merged["population"] = merged[POPULATION_COLUMN]
    merged["province"] = merged["PRUID"].map(PRUID_PROVINCE)
    merged["norm_name"] = merged["CSDNAME"].apply(normalize)

    candidates = merged[
        (~merged["DGUID"].isin(existing_dguids))
        & (~merged["CSDTYPE"].isin(EXCLUDE_CSDTYPES))
        & (merged["population"] >= args.min_population)
        & (~merged.apply(lambda r: already_tracked_by_name(r["norm_name"], r["province"]), axis=1))
    ].copy()

    candidates = candidates.sort_values("population", ascending=False)
    candidates = candidates[["CSDNAME", "CSDTYPE", "province", "population", "DGUID"]]
    candidates.to_csv(OUTPUT_CSV, index=False)

    print(f"Wrote {OUTPUT_CSV}")
    print(f"{len(candidates)} candidate(s) above population {args.min_population}, not currently in providers.csv")


if __name__ == "__main__":
    sys.exit(main())
