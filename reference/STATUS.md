# Project status (for session handoff)

Recreating StatCan's Canadian Cycling Network Database with updated/expanded data. See README.md for the high-level input/output summary.

## Locked in
- Terminology: **provider** (municipal/regional/provincial/other data publisher) vs **source** (one specific dataset for one domain, e.g. cycling). **Concordance** (not "crosswalk") for the source-class → Can-BICS mapping table.
- Repo currently holds three logically independent parts, each meant to become its own repo later: this project (root), `providers-directory/` (cross-project provider list), `lode/` (future generic pipeline package). Their internal layout is still evolving — do not treat current folder names as final.
- Config/state format: YAML per entity (one file per source/provider), CSV for the flat providers directory. No DB — but schemas are written to make a later DB migration cheap.
- Geo stack: geopandas/shapely, no DuckDB.
- `segment_id` is unique per pipeline run only — source datasets change their own IDs across years, so no cross-year join key is assumed.
- Each yearly run is a standalone snapshot (fresh clone, redownload, re-map). No merging/appending across years.
- CSD assignment is a pure spatial join (segment midpoint → CSD), independent of provider metadata. Provider-level `csduids` are for QA/documentation only.

## Not yet decided
- **Pipeline stages/steps** — discussed only as a rough sketch (ingest → filter → CSD join → classify → length → aggregate), not finalized.
- Repo folder structure beyond the 3-way split above.
- Column-mapping workflow (semi-auto + manual review) — not designed.
- Concordance-building workflow — not designed. Precedent found: the 2024 release's `classification_dictionary.csv` stores one manually-found Street View URL per (municipality, source_class) as its validation method — likely worth reusing directly instead of building a bespoke tool.
- `lode` package — not started (README placeholder only).

## Built so far
- `reference/canbics_classification.md` — Can-BICS facility definitions + comfort tiers (High/Medium/Low/Non-conforming), sourced from chatrlab.ca.
- `schema/network_segments.yaml` — target schema for the segment-level output.
- `schema/sources.yaml` + `sources/on_toronto_cycling.yaml` — source registry schema + one real entry (Toronto, `data/raw/on_toronto_cycling/`, raw gpkg downloaded).
- `providers-directory/schema/providers.yaml` + `providers.csv` — provider registry schema + one real entry (Toronto; `csduid`/`population` filled from memory, need verification).
- `canadian_cycling_network_database/` (gitignored) — the actual 2024 StatCan release, used as a baseline/precedent to sanity-check our schema design.

## Next steps
1. Manually build out `providers-directory/providers.csv`: bulk-seed from StatCan's CSD list (prioritized by population), reuse 2024 release's `data_sources.csv` as a head start, add the 13 provincial portals.
2. Draft `schema/concordance.yaml` and `schema/summary.yaml`.
3. Build a profiling tool (columns/dtypes/geometry/CRS + sample values per column) and run it against the Toronto raw file.
4. Design column-mapping workflow (semi-auto rules + manual review).
5. Design concordance workflow (semi-auto rules + manual review).
6. Design pipeline stages properly (currently just a rough sketch) and start scaffolding `lode/` once patterns stabilize across a few sources.

## Other notes

- added a file sources checklist - which we can use as basis for populating providers.csv
- might be a good ideea to have a script or something to download raw ancillary data files, such as CSD geometries, population, etc.
