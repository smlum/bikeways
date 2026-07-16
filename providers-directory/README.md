# Providers Directory

Canonical, cross-project source of truth for Canadian data providers — municipalities, regions, provinces, and other bodies that publish open geospatial data. Domain-agnostic: this list is reused by the bikeways project and any future project (e.g. pedestrian infrastructure) rather than re-derived per project.

Each project layers its own domain-specific tracking (has a cycling dataset been found for this provider? what's the URL?) on top, referencing `provider_id` — it does not duplicate or override facts recorded here.

- `providers.csv` — the directory itself. Schema: `schema/providers.yaml`.

Currently lives inside the `bikeways` repo for convenience; the intent is to split it into its own repo once it's established, so it can be depended on independently.
