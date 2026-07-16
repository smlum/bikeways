# Bikeways

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
3. classification crosswalk dictionary (municipal → CanBICS) (CSV) 
4. metadata: data source list + column/data dictionary.