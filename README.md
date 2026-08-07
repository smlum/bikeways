# Bikeways

Code and tools to build a national cycling network dataset from Canadian municipal data sources.

## Repo structure

This project uses the [lode](https://github.com/smlum/lode) package to implement the data pipeline, which is included as a **git submodule**. 


- This project (root: `reference/`, `schema/`, `sources/`, `data/`, `WORKFLOW.md`) — configuration and data specific to building the cycling network dataset: Can-BICS reference material, target schemas, per-source registry entries, raw downloads.
- `providers-directory/` — canonical, cross-project directory of Canadian data providers (municipal/regional/provincial). Domain-agnostic; reused by any future project, not just this one.
- `lode/` — reusable, domain-agnostic pipeline code and tools (ingestion, column mapping, spatial join, classification, aggregation) that this project's config plugs into. Its own repo, included here as a **git submodule**.
- `sources/` — per-source configuration files and metadata
- `scripts/` — one-off, project-specific scripts

### lode package



## Setup

```
git clone --recurse-submodules <this-repo-url>
# or, if already cloned: git submodule update --init

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e ./lode
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

## Data collection checklist

Working through `providers-directory/providers.csv` to find a cycling dataset per provider.
See [WORKFLOW.md](WORKFLOW.md#1-data-collection) for the full step-by-step. Quick start, from
the repo root (needs `lode` installed — see [Setup](#setup)):

```
lode tools checklist sync       # build/update sources/checklist.csv
lode tools checklist review     # then open http://localhost:8642 — browse, mark found, generate/edit yaml metadata
lode tools checklist process    # stamps checked_date for rows checked by hand outside the UI
```

## Classification review tool

`tools/classification-review/` lets you spot-check *classification* output — a classified
network dataset's (municipality, class) groups — by sampling random points and eyeballing them
in Street View. Assumes the [Setup](#setup) venv is already active. Run everything from the
repo root, no `cd` needed:

```
python3 tools/classification-review/sample_points.py --config tools/classification-review/config/cycle_network_2024.yaml
cp tools/classification-review/web/config.example.js tools/classification-review/web/config.js  # add your Google Maps API key
python3 -m http.server 8000 --directory tools/classification-review/web
```

Then open `http://localhost:8000`. See
[tools/classification-review/README.md](tools/classification-review/README.md)
for details (getting an API key, filters, current limitations).