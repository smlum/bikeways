# classification-review

Manual QA tool for checking *classification* output specifically: for each (municipality,
source classification) group in a classified cycling-network dataset, sample a few random
points along the line geometry and let a human eyeball them in Street View to check the
classification looks right. (Other review tools covering other concerns may live alongside
this one later — this one is scoped to classification only.)

Same idea as the precedent in `canadian_cycling_network_database/classification_dictionary.csv`
(one hand-found Street View link per municipality/source_class), just automated and scaled
to 3 random samples per group with an actual review UI instead of manual link-hunting.

Self-contained for now; if the sampling/column-mapping approach generalizes well it's a
candidate to move into `lode/` later, per the repo's usual pattern of graduating things
once they stabilize.

## How it works

1. **`sample_points.py`** (Python/geopandas) reads a vector file (gpkg, shapefile, geojson,
   or geoparquet — anything `geopandas` can read), groups rows by whatever columns you
   configure, and for each group picks N random points along the line geometry (weighted
   by segment length) plus a facing direction for the Street View camera. Output is a
   `manifest.json`.
2. **`web/`** is a static page: load `manifest.json`, step through each group, view the
   sample points in an embedded Street View panorama, and mark each as
   correct / incorrect / unsure / no imagery, with an optional note.

Column names and grouping are config-driven (see `config/cycle_network_2024.yaml`) so this
isn't locked to the 2024 StatCan release's schema — a different source with different
column names, or a parquet file instead of gpkg, just needs its own config file.

## Setup

Uses the shared repo-root venv — see the [main README](../README.md#setup). Everything
below is run from the repo root, not from inside `classification-review/`.

## Generating a manifest

```
source .venv/bin/activate
python3 classification-review/sample_points.py --config classification-review/config/cycle_network_2024.yaml
```

This generates one manifest covering every (municipality, source_class) group in the
dataset — for the 2024 release that's 373 groups / ~1,100 sample points, only ~250KB, so
there's no need to regenerate per municipality. Use the filter box in the web UI's
sidebar to jump to a specific municipality or class instead. Only re-run the script if
you change `n_samples`/the seed in the config, or the underlying source data changes.

Flags for quick iteration while developing (e.g. testing on a smaller slice):

```
--filter municipality=Calgary     # repeatable, restricts to matching rows
--limit-groups 10                 # only keep the first N groups in the output
```

This writes `classification-review/web/manifest.json` (gitignored — it's derived, and
depends on the random seed/local data you have).

## Running the review page

The Maps JavaScript API needs the page served over http, not opened as a `file://` URL.
Run from the repo root — no need to `cd` into `classification-review/web`.

1. Copy `classification-review/web/config.example.js` to `classification-review/web/config.js`
   and paste in your Google Maps API key (gitignored — don't commit it).
2. `python3 -m http.server 8000 --directory classification-review/web`
3. Open `http://localhost:8000`.

### Getting an API key

1. In [Google Cloud Console](https://console.cloud.google.com/), create (or reuse) a project.
2. Enable the **Maps JavaScript API** (this includes the Street View panorama service —
   no separate Street View API needed for the interactive embed used here).
3. Enable billing on the project. Usage here is tiny (a handful of panorama loads per
   review session), well within the free monthly credit, but Google requires a billing
   account attached regardless.
4. Create an API key under **APIs & Services → Credentials**. For local use, restrict it
   to HTTP referrers like `localhost:8000/*` and `127.0.0.1:8000/*`.

## Current state / not yet decided

- **Persistence is localStorage-only.** Verdicts are saved in the browser as you go (so a
  reload won't lose progress) and can be exported to a JSON file via the "Export reviews"
  button. There's no backend and no defined schema for where reviews ultimately live —
  that depends on decisions not yet made about the concordance/classification storage
  format, so it's deliberately left as an export step for now rather than guessed at.
- No merge-back step yet from an exported reviews JSON into the classification dictionary
  — add once the storage format for reviews/concordance is decided.
