#!/usr/bin/env python3
"""Batch-process checklist.csv after a round of manual browsing.

Pass 1 is manual, directly in checklist.csv, no scripts involved: for each
row, check the portal. Found something -> paste the dataset page URL into
source_url. Nothing there -> type any non-blank value (e.g. "x") into
checked. Found a second dataset for the same provider -> duplicate that row
and put the second URL in the copy.

This script is pass 2, run once after a batch of rows have been updated:
- Rows with a new source_url and no source_ids yet: scaffold
  <sources-dir>/<source_id>.yaml (dataset_page_url prefilled from
  source_url, license/contact from providers.csv), and record source_ids +
  checked_date. source_id defaults to "<provider_id>_cycling"; a second row
  for the same provider gets "_cycling_2", a third "_cycling_3", etc.
- Rows with checked set and no checked_date yet: just stamp checked_date.

Safe to re-run: rows that already have source_ids, or an existing yaml file,
are left alone.

Usage:
    python process_checklist.py [--checklist-csv path] [--providers-csv path] [--sources-dir path]
"""

import argparse
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from _paths import find_repo_root

REPO_ROOT = find_repo_root(Path(__file__).resolve())
DEFAULT_PROVIDERS_CSV = REPO_ROOT / "providers-directory" / "providers.csv"
DEFAULT_CHECKLIST_CSV = REPO_ROOT / "sources" / "checklist.csv"
DEFAULT_SOURCES_DIR = REPO_ROOT / "sources" / "datasets"


def next_slug(n: int) -> str:
    return "cycling" if n == 0 else f"cycling_{n + 1}"


def scaffold(sources_dir: Path, provider_id: str, source_url: str, provider_row, slug: str):
    source_id = f"{provider_id}_{slug}"
    out_path = sources_dir / f"{source_id}.yaml"
    if out_path.exists():
        return None, f"{out_path} already exists, skipped"
    source = {
        "source_id": source_id,
        "provider_id": provider_id,
        "dataset_page_url": source_url,
        "download_url": "",
        "format": "",
        "license_name": provider_row["portal_license_name"] if provider_row is not None else "",
        "license_url": provider_row["portal_license_url"] if provider_row is not None else "",
        "contact": provider_row["contact"] if provider_row is not None else "",
        "source_updated_date": "",
        "retrieved_date": str(date.today()),
        "data_dictionary_url": "",
        "raw_filename": "",
        "notes": "",
    }
    with open(out_path, "w") as f:
        yaml.dump(source, f, sort_keys=False, allow_unicode=True)
    return source_id, None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--checklist-csv", type=Path, default=DEFAULT_CHECKLIST_CSV)
    parser.add_argument("--providers-csv", type=Path, default=DEFAULT_PROVIDERS_CSV)
    parser.add_argument("--sources-dir", type=Path, default=DEFAULT_SOURCES_DIR)
    args = parser.parse_args()

    if not args.checklist_csv.exists():
        raise FileNotFoundError(f"{args.checklist_csv} doesn't exist — run sync_checklist.py first")

    checklist = pd.read_csv(args.checklist_csv, dtype=str).fillna("")
    providers = pd.read_csv(args.providers_csv, dtype=str).fillna("").set_index("provider_id")
    today = str(date.today())

    # How many sources each provider already has, so a second/third row gets a distinct slug.
    existing_count = (
        checklist[checklist["source_ids"] != ""].groupby("provider_id").size().to_dict()
    )

    created, skipped, stamped = [], [], []

    for i, row in checklist.iterrows():
        provider_id = row["provider_id"]

        if row["source_url"] and not row["source_ids"]:
            provider_row = providers.loc[provider_id] if provider_id in providers.index else None
            n = existing_count.get(provider_id, 0)
            source_id, err = scaffold(args.sources_dir, provider_id, row["source_url"], provider_row, next_slug(n))
            if err:
                skipped.append((provider_id, err))
                continue
            existing_count[provider_id] = n + 1
            checklist.at[i, "source_ids"] = source_id
            checklist.at[i, "checked_date"] = today
            created.append(source_id)

        elif row["checked"] and not row["checked_date"]:
            checklist.at[i, "checked_date"] = today
            stamped.append(provider_id)

    checklist.to_csv(args.checklist_csv, index=False)

    print(f"Created {len(created)} source(s): {', '.join(created) if created else '(none)'}")
    print(f"Stamped checked_date for {len(stamped)} row(s) with nothing found")
    if skipped:
        print(f"Skipped {len(skipped)}:")
        for provider_id, err in skipped:
            print(f"  - {provider_id}: {err}")


if __name__ == "__main__":
    sys.exit(main())
