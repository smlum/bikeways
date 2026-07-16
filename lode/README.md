# lode

Reusable, domain-agnostic pipeline code for turning heterogeneous linear-network open data (cycling, pedestrian, ...) into a standardized, classified, spatially-joined network dataset.

Not specific to bikeways: projects supply their own target schema and classification system (e.g. Can-BICS for cycling); this package supplies the shared mechanics — ingestion adapters, column-mapping tooling, spatial join to census subdivisions, length calculation, aggregation, and output writers.

Currently developed inside the `bikeways` repo; the intent is to split it into its own installable package/repo once the interface stabilizes.
