# lode

The lode package is a collection of tools for creating lode datasets.

Currently developed inside the `bikeways` repo; the intent is to split it into its own installable package/repo once the interface stabilizes.

## Aims for a `lode` package

To help with these common tasks across datasets, this packaged is intended to provide:

1. A common data providers list
2. Tools to assist with manual steps in the workflow ()
3. A pipeline to automate the processing of data from raw to processed
4. Reference data and fetch scripts (CSDs, population, etc)

## Orchestration

The package will contain a single cli entrypoint, `lode`, which will orchestrate the various tools and pipelines.

### Pipeline

### Custom steps

Custom scripts can be run by the orchestration tool, and will be run in the order specified in the config file. The scripts should be placed in `lode/pipeline` and should accept a single argument, the path to the repo root.

### Tools

Can be run using 

## Installation

```bash
# install lode package
pip install ...
```

## Setup

```bash
# install dependencies
pip install -r requirements.txt
``` 

