# Lab 1: Germany Grid Bottleneck Model

This folder is independent from the rest of the repository and does not use Loom.

## What It Does

- Downloads public raw data into `lab1/raw_data/`.
- Builds an open-data approximation of current German transmission bottlenecks.
- Exports model outputs into `lab1/processed/`.
- Builds a static data page in `lab1/web/`.

## Data Sources

- Germany high-voltage topology: `ComplexNetTSP/Power_grids`, derived from OpenStreetMap / SciGRID-style processing.
- Near-real-time Germany generation and load: Fraunhofer ISE Energy-Charts API.
- German market and control-area hourly validation data: Bundesnetzagentur SMARD API.

Full source URLs and local file paths are recorded in:

```text
lab1/raw_data/source_catalog.json
```

## Run

```bash
python3 lab1/scripts/download_data.py
python3 lab1/scripts/build_model.py
```

Then open:

```text
lab1/web/index.html
```

## Model

The model is a transparent open-data DC load-flow approximation:

- Uses the largest connected German high-voltage network component.
- Parses multi-circuit OSM line records into equivalent impedance and thermal capacity.
- Allocates actual national generation and load spatially by technology-specific heuristics.
- Balances net imports/exports on border-proximate substations.
- Solves a DC power-flow and ranks bottlenecks by utilization and line length.

This is suitable for screening and exploration. It is not an official TSO operational
model because current full German asset parameters, switching state, remedial actions,
and redispatch dispatch files are not fully public.
