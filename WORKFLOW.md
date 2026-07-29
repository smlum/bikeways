# Workflow

## General notes for `lode` package

- Should deal with point, line, polygon data. Some steps will be geometry-specific — pipeline may run one geometry type at a time to keep this simple, rather than mixing within a run.
- Deal with multiple input formats (geopackage, parquet, geojson, json, csv, shp, etc)
- Work across several domains. Test case here is bike lane data. Next up will be pedestrian. Other might be healthcare facilities.
- Includes:
    1. Providers list and common column schema (copyable)
    2. Pipeline codebase (preprocess, process, validate)
    4. Workflow tools (classification, column map, dashboard)
    5. Reference data + fetch scripts (StatCan CSD, population)

## 1. Data collection

Providers live in `providers-directory/providers.csv`. Checklist + per-source metadata live in
`sources/` (`checklist.csv`, `datasets/*.yaml`); the tools that manage them are in
`lode/src/lode/tools/checklist/`.

**Workflow**
- `python sync_checklist.py` — builds/updates `checklist.csv` from `providers.csv`. Safe to
  re-run any time; never loses progress.
- `python web/server.py` (http://localhost:8642) — one tool, two things:
  - Browse each row's portal and record what you find: Found → `source_url`, Nothing → `checked`.
    `prior_url` (e.g. a 2024 CCND lead) is offered as a starting point but never overwritten by
    these actions, so a mistaken "not found" can't destroy it. As soon as a row is Found,
    `data/raw/<source_id>/` is created so there's somewhere to land the download.
  - Once found, the row's Metadata column lets you generate `sources/datasets/<id>.yaml`
    (deliberately on demand, not automatic) and fill in the rest (`format`, `raw_filename`,
    etc.) in a modal — including a "Detect" button that reads whatever you've dropped in
    `data/raw/<source_id>/` to prefill `format`/`raw_filename`.
- `python process_checklist.py` — just stamps `checked_date` for rows checked off by hand
  outside the UI (e.g. direct CSV edits). Never touches yaml.

**Notes**
- `checked`/`checked_date` are tracked distinctly from what was found, so future years know
  what's already been reviewed, not just what's been found so far.
- A provider with more than one dataset gets a duplicated checklist row, not a list column.
- `provider_id` must stay unique in `providers.csv` — when two distinct providers share a
  name (e.g. a city and the surrounding region/county), disambiguate with a suffix rather
  than merging them onto one id; it's also the basis for `source_id` and the
  `data/raw/<source_id>/` folder, so a collision there would collide downstream too.

## 2. Data inspection

**Input**
- Raw data files

**Output**
- Log file with report for each raw data file:
  - Number of rows
  - Loaded correctly
  - For each column:
    - Number of unique values
    - Type
    - Number of nulls
    - 3 sample points in a comma separated list (max 25 chars each)
  - Geometry
  - CRS
  - Formatting (UTF-8?)
- Column mapping file(s) (automated)
- Column mapping file(s) (manually reviewed and locked in)

**Workflow**
- Run a script that analyses raw data directory
- Review automated column mapping
- Generate manually verified or modified column mapping

## 3. Data preprocessing

**Input**
- Raw data files

**Output**
- Cleaned data files
  - Standardize format
  - Standardize column names (using column mapping from previous step)
  - Standardize geometry
  - Standardize CRS
  - Standardize formatting (UTF-8?)
  - Deal with special characters
  - Standardize nulls, blank spaces, etc
  - Basic deduplication (within files)
  - Assign ID (unique within a run only — not stable across years/vintages, segments can change)
- Log of results
  - Rows per file

**Workflow**
- Run script

## 4. Data classification

**Input**
- Cleaned data files
- Previous classification files (e.g. 2024 mapping)
- Classification rules config (project-specific, rules-based matching)

**Output**
- Automated classification mapping
- Reviewed/locked classification mapping

**Workflow**
- Script applies rules-based matching against source values → automated classification
- UI to inspect source values and verify/correct the automated mapping (this is `classification-review`, extended to drive initial assignment, not just post-hoc QA)
  - For all unique values of specified columns to be classified:
    - Number of rows
    - Calculated length (rough is fine)
    - Specified number of sample values (default 3)
    - Google Street View
    - Previous classification (if poss)
  - Manual review/correction where automated matching fails

**Notes**
- Source class may need multiple source columns combined to assign one target class (not always a single 1:1 column)
- May need to classify more than one target attribute — e.g. Can-BICS class and surface material/type — not just one

## 5. Data processing

**Input**
- Cleaned data files
- StatCan CSD file

**Output**
- Processed data files
- Logs
  - Summary from each step — what changed
  - Summary before/after filtering. Transparent on rows dropped for what reason

**Workflow**
- Run pipeline orchestrator script to run each stage

**Steps**
- Per provider file, processed concurrently:
  - Apply classifications (using classification mapping file from previous step)
  - Filter unwanted data
  - Calculate lengths along line geometry
  - Assign CSD (using StatCan CSD geometry file)
- Merge — combine all provider files into one dataset
- Deduplication — spatial, across the merged data

**Notes**
- These steps are specific to bikeways. Package should be able to accommodate new steps, or choice to not run certain steps — i.e. modular.
- If some steps are very long, option to produce intermediate data?
- Still missing: final aggregation/output step (summary CSV by municipality, concordance dictionary, metadata dictionary) — TBD

## 6. Data validation

**Input**
- Processed data
- Previous data (optional) — prior vintage's completed output, loaded as a static file (e.g. 2019, 2024), not from a shared/live pipeline
- OSM data (optional)

**Output**
- Pass/fail result
- Logs

**Workflow**
- Run automated sanity checks/tests against the data, report yes/no plus details in the log
- Specific checks TBD

## 7. Data visualization

**Input**
- Data from any pipeline stage (raw through processed) — useful for troubleshooting without a GIS tool, not just final output

**Output**
- Plotly Dash app
  - Map plotting data
    - Click on a point opens tooltip with column: value pairs
    - Tooltip has option to open a Google Street View link from that point (can point externally and open in new tab)
  - Column inspection
    - Number of unique values
    - Type
    - Number of nulls
    - 3 sample points
  - Table view — sort
  - Filtering
    - Apply to map and table?
    - By specified (categorical?) columns
