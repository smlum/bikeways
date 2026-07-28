#!/usr/bin/env python3
"""Fetch a StatCan data table (CSV-in-zip) and convert it to parquet.

Same one-off role as fetch_csd.py, but for tabular tables (e.g. population
counts) rather than boundary shapefiles. StatCan table downloads ship as a
zip containing the data CSV plus a large "_MetaData" CSV — this script keeps
only the data CSV and writes it through unchanged (no column renaming/
selection here; that's the matching/join script's job, not the fetch step).

Usage:
    python fetch_table.py --dataset population_2021_csd

Dataset URLs are looked up from datasets.yaml (next to this script) by key;
add new entries there rather than passing a raw URL.
"""

import argparse
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd

from _datasets import DEFAULT_CONFIG, load_dataset, resolve_output


def download_zip(url: str, dest_dir: Path) -> Path:
    zip_path = dest_dir / "table.zip"
    print(f"Downloading {url}")
    urlretrieve(url, zip_path)
    return zip_path


def extract_data_csv(zip_path: Path, dest_dir: Path) -> Path:
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest_dir)
    csv_files = [p for p in dest_dir.rglob("*.csv") if "metadata" not in p.stem.lower()]
    if not csv_files:
        raise FileNotFoundError(f"No non-metadata .csv file found inside {zip_path}")
    if len(csv_files) > 1:
        raise ValueError(f"Expected one data .csv file, found {len(csv_files)}: {csv_files}")
    return csv_files[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", required=True, help="Dataset key in datasets.yaml, e.g. population_2021_csd")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Path to datasets.yaml (default: next to this script)")
    parser.add_argument("--output", type=Path, help="Output parquet path (default: 'output' entry in datasets.yaml for this dataset)")
    args = parser.parse_args()

    dataset = load_dataset(args.dataset, args.config)
    output = args.output or dataset.get("output")
    if not output:
        raise ValueError(f"No --output given and no default 'output' set for dataset '{args.dataset}' in {args.config}")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        zip_path = download_zip(dataset["url"], tmp_dir)
        csv_path = extract_data_csv(zip_path, tmp_dir)

        print(f"Reading {csv_path}")
        df = pd.read_csv(csv_path, encoding="utf-8-sig")

        print(f"Rows: {len(df)}")
        print(f"Columns: {list(df.columns)}")

        df.to_parquet(output)
        print(f"Wrote {output}")


if __name__ == "__main__":
    sys.exit(main())
