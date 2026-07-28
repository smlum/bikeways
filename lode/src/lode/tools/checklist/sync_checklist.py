#!/usr/bin/env python3
"""Create/update checklist.csv from a providers directory's providers.csv.

Generic — not cycling-specific, reusable as-is by a future project.

name/portal_url/geography_level/province are informational, refreshed from
providers.csv on every run (edits to them here are overwritten — go fix
providers.csv instead). source_url/checked/checked_date/source_ids/notes are
the actual working state and are preserved across runs, matched by
provider_id — including when a provider has more than one row (duplicate a
row by hand when a second dataset is found on the same portal).

Usage:
    python sync_checklist.py [--providers-csv path] [--checklist-csv path]
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

from _paths import find_repo_root

REPO_ROOT = find_repo_root(Path(__file__).resolve())
DEFAULT_PROVIDERS_CSV = REPO_ROOT / "providers-directory" / "providers.csv"
DEFAULT_CHECKLIST_CSV = REPO_ROOT / "sources" / "checklist.csv"
GEOGRAPHY_LEVEL_ORDER = ["national", "province", "region", "municipality", "other"]
WORK_COLUMNS = ["source_url", "checked", "checked_date", "source_ids", "notes"]
COLUMN_ORDER = [
    "checked", "provider_id", "portal_url", "source_url",
    "name", "geography_level", "province", "checked_date", "source_ids", "notes",
]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--providers-csv", type=Path, default=DEFAULT_PROVIDERS_CSV)
    parser.add_argument("--checklist-csv", type=Path, default=DEFAULT_CHECKLIST_CSV)
    args = parser.parse_args()

    providers = pd.read_csv(args.providers_csv, dtype=str).fillna("")
    info = providers[["provider_id", "name", "portal_url", "geography_level", "province"]]

    if args.checklist_csv.exists():
        prior = pd.read_csv(args.checklist_csv, dtype=str).fillna("")
        work = prior[["provider_id", *WORK_COLUMNS]]
    else:
        work = pd.DataFrame(columns=["provider_id", *WORK_COLUMNS])

    checklist = info.merge(work, on="provider_id", how="left").fillna("")

    checklist["geography_level"] = pd.Categorical(
        checklist["geography_level"], categories=GEOGRAPHY_LEVEL_ORDER, ordered=True
    )
    checklist = checklist.sort_values(
        ["geography_level", "province", "name"], kind="stable"
    ).reset_index(drop=True)
    checklist["geography_level"] = checklist["geography_level"].astype(str)
    checklist = checklist[COLUMN_ORDER]

    args.checklist_csv.parent.mkdir(parents=True, exist_ok=True)
    checklist.to_csv(args.checklist_csv, index=False)

    new_count = len(set(info["provider_id"]) - set(work["provider_id"]))
    print(f"Wrote {args.checklist_csv}")
    print(f"{new_count} new provider(s) added, {len(checklist)} total rows")


if __name__ == "__main__":
    sys.exit(main())
