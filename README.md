# Bikeways

## Repo structure

This repo currently contains three logically independent things, each destined to move to its own repo once established:

- **This project** (root: `reference/`, `schema/`, `sources/`, `data/`) — configuration and data specific to building the cycling network dataset: Can-BICS reference material, target schemas, per-source registry entries, raw downloads.
- **`providers-directory/`** — canonical, cross-project directory of Canadian data providers (municipal/regional/provincial). Domain-agnostic; reused by any future project, not just this one.
- **`lode/`** — reusable, domain-agnostic pipeline code (ingestion, column mapping, spatial join, classification, aggregation) that this project's config plugs into.
- **`classification-review/`** — manual QA tool for spot-checking Can-BICS classifications against Street View. See below. (Other review tools covering different concerns may join it as siblings later.)

## Setup

Python environment:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Plan

### Input 

heterogeneous municipal cycling network data (GeoJSON/Shapefile/parquet/JSON/etc.), each with its own infrastructure classification scheme.

### Pipeline

1. ingest → filter to relevant cycling infrastructure 
2. spatial join to census subdivisions (CSDs) 
3. classify infrastructure into standardized categories (CanBICS)
4. compute segment lengths 
5. aggregate to city-level summaries → clean/validate.

### Outputs: 

1. geospatial network dataset (parquet), 
2. summary table of infrastructure length by municipality (CSV), 
3. classification concordance dictionary (source class → Can-BICS) (CSV) 
4. metadata: data source list + column/data dictionary.

## Classification review tool

`classification-review/` lets you spot-check *classification* output — a classified network
dataset's (municipality, class) groups — by sampling random points and eyeballing them in
Street View. Assumes the [Setup](#setup) venv is already active. Run everything from the repo
root, no `cd` needed:

```
python3 classification-review/sample_points.py --config classification-review/config/cycle_network_2024.yaml
cp classification-review/web/config.example.js classification-review/web/config.js  # add your Google Maps API key
python3 -m http.server 8000 --directory classification-review/web
```

Then open `http://localhost:8000`. See
[classification-review/README.md](classification-review/README.md) for details (getting an
API key, filters, current limitations).