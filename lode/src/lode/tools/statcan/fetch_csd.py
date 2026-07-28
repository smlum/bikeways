#!/usr/bin/env python3
"""Fetch a StatCan census geography boundary file and convert it to geoparquet.

One-off setup script, not part of the per-run pipeline: run it whenever a new
census vintage is needed, then point projects at the resulting geoparquet file
(e.g. for CSD spatial joins). Not specific to CSDs despite the name — any
StatCan cartographic boundary file (CSD, CD, province, etc.) shipped as a
zipped shapefile works the same way.

Usage:
    python fetch_csd.py --dataset csd_2021_cbf

Dataset URLs are looked up from datasets.yaml (next to this script) by key;
add new entries there rather than passing a raw URL.
"""

import argparse
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlretrieve

import geopandas as gpd

from _datasets import DEFAULT_CONFIG, load_dataset, resolve_output


def download_zip(url: str, dest_dir: Path) -> Path:
    zip_path = dest_dir / "boundary_file.zip"
    print(f"Downloading {url}")
    urlretrieve(url, zip_path)
    return zip_path


def extract_shapefile(zip_path: Path, dest_dir: Path) -> Path:
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest_dir)
    shp_files = list(dest_dir.rglob("*.shp"))
    if not shp_files:
        raise FileNotFoundError(f"No .shp file found inside {zip_path}")
    if len(shp_files) > 1:
        raise ValueError(f"Expected one .shp file, found {len(shp_files)}: {shp_files}")
    return shp_files[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", required=True, help="Dataset key in datasets.yaml, e.g. csd_2021_cbf")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Path to datasets.yaml (default: next to this script)")
    parser.add_argument("--output", type=Path, help="Output geoparquet path (default: 'output' entry in datasets.yaml for this dataset)")
    args = parser.parse_args()

    dataset = load_dataset(args.dataset, args.config)
    output = args.output or dataset.get("output")
    if not output:
        raise ValueError(f"No --output given and no default 'output' set for dataset '{args.dataset}' in {args.config}")
    output = resolve_output(output, __file__)
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        zip_path = download_zip(dataset["url"], tmp_dir)
        shp_path = extract_shapefile(zip_path, tmp_dir)

        print(f"Reading {shp_path}")
        gdf = gpd.read_file(shp_path)

        print(f"Rows: {len(gdf)}")
        print(f"CRS: {gdf.crs}")
        print(f"Columns: {list(gdf.columns)}")

        gdf.to_parquet(output)
        print(f"Wrote {output}")


if __name__ == "__main__":
    sys.exit(main())
