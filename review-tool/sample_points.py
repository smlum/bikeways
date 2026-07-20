#!/usr/bin/env python3
"""Sample random points along line geometries, grouped by classification, for Street View review.

Config-driven so it isn't locked to one source's column names or file format
(gpkg/shapefile/geojson via geopandas.read_file, or geoparquet via geopandas.read_parquet).
"""

import argparse
import json
import math
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import yaml


def load_input(path: Path) -> gpd.GeoDataFrame:
    if path.suffix == ".parquet":
        return gpd.read_parquet(path)
    return gpd.read_file(path)


def ensure_projected(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    if gdf.crs is None:
        raise ValueError("Input has no CRS defined")
    if gdf.crs.is_geographic:
        return gdf.to_crs(gdf.estimate_utm_crs())
    return gdf


def explode_to_lines(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.explode(index_parts=False)
    return gdf[gdf.geometry.geom_type == "LineString"]


def bearing(p1, p2) -> float:
    dx, dy = p2.x - p1.x, p2.y - p1.y
    return (math.degrees(math.atan2(dx, dy)) + 360) % 360


def sample_group(group: gpd.GeoDataFrame, n: int, rng: np.random.Generator, id_col: str | None):
    group = ensure_projected(group)
    lengths = group.geometry.length.to_numpy()
    total = lengths.sum()
    if total <= 0:
        return []

    weights = lengths / total
    picks = rng.choice(len(group), size=n, p=weights)
    to_wgs84 = group.crs.to_epsg() != 4326

    samples = []
    for row_pos in picks:
        row = group.iloc[row_pos]
        line = row.geometry
        dist = rng.uniform(0, line.length)
        point = line.interpolate(dist)

        d1, d2 = max(dist - 1, 0), min(dist + 1, line.length)
        heading = bearing(line.interpolate(d1), line.interpolate(d2))

        point_wgs84 = (
            gpd.GeoSeries([point], crs=group.crs).to_crs("EPSG:4326").iloc[0] if to_wgs84 else point
        )

        samples.append({
            "id": str(row[id_col]) if id_col else None,
            "lat": point_wgs84.y,
            "lng": point_wgs84.x,
            "heading": round(heading, 1),
        })
    return samples


def total_length_km(group: gpd.GeoDataFrame, length_col: str | None) -> float:
    if length_col:
        return float(group[length_col].sum())
    return float(ensure_projected(group).geometry.length.sum() / 1000)


def build_manifest(gdf, group_by, label_col, id_col, length_col, n_samples, n_reserve, seed):
    rng = np.random.default_rng(seed)
    gdf = explode_to_lines(gdf)

    groups = []
    for key, group in gdf.groupby(group_by, dropna=False):
        key = key if isinstance(key, tuple) else (key,)
        # Sample extra "spare" points up front so the review page's "try another point"
        # button can swap in a fresh one without needing the raw geometry client-side.
        samples = sample_group(group, n_samples + n_reserve, rng, id_col)
        if not samples:
            continue

        entry = dict(zip(group_by, key))
        if label_col:
            non_null = group[label_col].dropna()
            entry["label"] = non_null.mode().iat[0] if not non_null.empty else None
        entry["n_features"] = len(group)
        entry["length_km"] = round(total_length_km(group, length_col), 2)
        entry["samples"] = samples[:n_samples]
        entry["spare_samples"] = samples[n_samples:]
        groups.append(entry)
    return groups


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument(
        "--filter", action="append", default=[], metavar="COL=VALUE",
        help="Restrict to rows where COL == VALUE (repeatable), e.g. --filter municipality=Calgary",
    )
    parser.add_argument(
        "--limit-groups", type=int, default=None,
        help="Only keep the first N groups in the output (for quick test runs)",
    )
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text())
    base_dir = args.config.parent

    input_path = (base_dir / config["input"]["path"]).resolve()
    columns = config["columns"]
    sampling = config.get("sampling", {})
    output_path = (base_dir / config["output"]["manifest"]).resolve()

    gdf = load_input(input_path)
    if columns["geometry"] != gdf.geometry.name:
        gdf = gdf.rename_geometry(columns["geometry"])

    for filt in args.filter:
        col, _, value = filt.partition("=")
        gdf = gdf[gdf[col].astype(str) == value]

    if gdf.empty:
        sys.exit("No rows left after filtering; check --filter values.")

    groups = build_manifest(
        gdf,
        group_by=columns["group_by"],
        label_col=columns.get("label"),
        id_col=columns.get("id"),
        length_col=columns.get("length"),
        n_samples=sampling.get("n_samples", 3),
        n_reserve=sampling.get("n_reserve", 5),
        seed=sampling.get("seed"),
    )

    if args.limit_groups:
        groups = groups[: args.limit_groups]

    manifest = {
        "source_file": str(input_path),
        "group_by": columns["group_by"],
        "groups": groups,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2))
    print(f"Wrote {len(groups)} groups ({sum(len(g['samples']) for g in groups)} sample points) to {output_path}")


if __name__ == "__main__":
    main()
