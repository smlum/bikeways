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

In this step, we collect data from various sources. 

To start, we have our source list from our previous iteration of the data. Second, we can search our provider list for new data. 

The workflow is to first generate a sources check list from our list of previous sources and the provider list. 
One a source is found, we:

1. Download the data file to `data/raw/provider`
2. Mark the source as checked in our sources checklist
3. Fill out metadata for the source. Some of this can be automated, but some will require manual input.

**Input**
- Data providers master directory

**Output**
- Collected data
- Metadata files

**Workflow**
- Go through sources checklist, search for new data
- Manually search websites for new data
- If data found:
  - Download file
  - Mark on sources checklist
  - Fill out metadata — can we part-automate? (e.g. CKAN/ArcGIS Hub portals expose metadata APIs — could pre-fill format/license/updated-date for those; still manual for one-off pages)
- Checklist should track checked-date, not just found/not-found, so future years know what's already been checked (100+ entries — simple UI/workflow TBD)

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
