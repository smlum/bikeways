#!/usr/bin/env python3
"""One-off: seed checklist.csv's source_url from the prior (2024) CCND vintage.

Cycling-specific and one-off — not part of the reusable lode/tools/checklist
scripts. Matches CCND's data_sources.csv rows to checklist rows using the
same key convention as provider_id ("{province_territory}_{municipality}").
Only fills source_url where the checklist row's source_url is still blank,
never overwrites an existing one. When a provider has more than one CCND
dataset (e.g. "kitchener"/"kitchener_mup"), a second checklist row is
duplicated, matching the manual multi-source convention.

This only seeds source_url + a "prior vintage" note — it does not scaffold
yaml files or set checked_date; run process_checklist.py after this, same
as if you'd found these links by hand. Every legacy URL is 1-3 years old and
may be dead or superseded, so treat these as leads to verify, not confirmed
sources.

Usage:
    python reconcile_ccnd.py
"""

import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
CCND_CSV = REPO_ROOT / "data/reference/canadian_cycling_network_database/data_sources.csv"
CHECKLIST_CSV = REPO_ROOT / "sources/checklist.csv"


def main():
    if not CHECKLIST_CSV.exists():
        raise FileNotFoundError(f"{CHECKLIST_CSV} doesn't exist — run sync_checklist.py first")

    checklist = pd.read_csv(CHECKLIST_CSV, dtype=str).fillna("")
    ccnd = pd.read_csv(CCND_CSV, dtype=str).fillna("")

    matched, duplicated, unmatched, skipped_blank = [], [], [], []

    for _, ccnd_row in ccnd.iterrows():
        if not ccnd_row["source_url"]:
            skipped_blank.append(f"{ccnd_row['province_territory']}_{ccnd_row['municipality']}")
            continue

        provider_id = f"{ccnd_row['province_territory']}_{ccnd_row['municipality']}"
        year = ccnd_row["year_updated"]
        note = f"from {year} CCND vintage, needs re-verification" if year else "from prior CCND vintage, needs re-verification"

        matches = checklist.index[checklist["provider_id"] == provider_id]
        if len(matches) == 0:
            unmatched.append(provider_id)
            continue

        open_row = matches[checklist.loc[matches, "source_url"] == ""]
        if len(open_row) > 0:
            idx = open_row[0]
        else:
            # Every existing row already has a source_url — duplicate one for this lead.
            idx = len(checklist)
            checklist.loc[idx] = checklist.loc[matches[0]]
            checklist.at[idx, "source_url"] = ""
            checklist.at[idx, "source_ids"] = ""
            checklist.at[idx, "checked_date"] = ""
            duplicated.append(provider_id)

        checklist.at[idx, "source_url"] = ccnd_row["source_url"]
        existing_notes = checklist.at[idx, "notes"]
        checklist.at[idx, "notes"] = f"{existing_notes}; {note}" if existing_notes else note
        matched.append(provider_id)

    checklist.to_csv(CHECKLIST_CSV, index=False)

    print(f"Filled source_url for {len(matched)} row(s)")
    print(f"{len(duplicated)} required a duplicated row (provider already had a source_url)")
    print(f"{len(skipped_blank)} CCND row(s) had no source_url themselves, skipped")
    if unmatched:
        print(f"{len(unmatched)} CCND row(s) had no matching provider_id:")
        for pid in unmatched:
            print(f"  - {pid}")


if __name__ == "__main__":
    sys.exit(main())
