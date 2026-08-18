# Bikeways

Builds a national Canadian cycling-infrastructure dataset from municipal open-data sources, classified against the Can-BICS standard.

## Repo structure

At root:

- `lode.config.yaml` — project-specific configuration for the pipeline.
- `reference/` — Can-BICS reference material 
- `schema/` — target schemas for the final dataset
- `scripts/` — one-off, project-specific scripts
- `sources/` — per-source configuration files and metadata

External dependencies:

- `lode/` — reusable pipeline code and tools, included here as a **git submodule**.
- `ca-data-providers/` — cross-project directory of Canadian data providers, included here as a **git submodule**..

Generated during the pipeline: 

- `data/` — raw downloads and intermediate outputs

## Setup

Clone the repo (with submodules):

```bash
git clone --recurse-submodules https://github.com/smlum/bikeways.git
# or, if already cloned: git submodule update --init
```

Set up a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate # Linux/Mac
# .venv\Scripts\activate # Windows
pip install -r requirements.txt
pip install -e ./lode
```

## Workflow overview

A broad overview of the workflow is:

1. Collection
2. Inspection
3. Preprocessing (standardize columns, geometry, CRS, formatting, etc)
4. Classification 
5. Processing (filtering, assigning CSD, calculating lengths, merging, deduplication)
6. Validation
7. Data visualization
8. Dissemination 

### Outputs: 

1. Geospatial cycling network dataset (parquet) 
2. Summary table of infrastructure length by municipality (CSV) 
3. Classification concordance dictionary (source class → Can-BICS) (CSV) 
4. Metadata: data source list + column/data dictionary (CSV)

## Workflow

### 1. Data collection

Collection starts with a universal provider list. It outputs a completed checklist. 

The workflow for collection is: universal provider list → project-specific checklist derived from it → a tool (living in `lode`).

In more detail:

1. A central registry of Canadian data providers maintained in `providers-directory/` (soon to be in its own git repository). 

2. `lode tools checklist sync` — generates/updates sources/checklist.csv (project-specific, lives in bikeways) from providers.csv. Re-runnable, non-destructive.

3. `lode tools checklist review` (localhost:8642) — a workflow tool to:

    1.  Walk through provider by provider: open their portal, mark Found (records source_url) or Nothing (checked). 

    2. On Found, scaffolds `sources/<source_id>/metadata.yaml` on demand (conforming to `schema/sources.yaml`) and creates `data/raw/<source_id>/` for the download.

4. `lode tools checklist process` — just stamps checked_date for anything you checked off by hand outside the UI.

### 2. Data inspection

- `lode tools column-mapping` (localhost:8645) — inspects each source's raw file, suggests column-target matches, saves reviewed mappings to `sources/<source_id>/column_map.yaml`

### 3. Data preprocessing

- `lode pipeline run --stage preprocessing` — standardizes columns (via the column mapping above), geometry, and CRS; assigns per-run IDs

### 4. Data classification

`scripts/classification-review/` lets you spot-check *classification* output — a classified
network dataset's (municipality, class) groups — by sampling random points and checking them in Street View. 

### 5. Data processing

- `lode pipeline run --stage processing` — assigns CSD (StatCan geometry) and computes segment lengths
- `lode pipeline run --stage merge` — combines all sources into one dataset (`data/merged/network_segments.parquet`); spatial dedup not yet built

### 6. Data validation

### 7. Data visualization

### 8. Dissemination