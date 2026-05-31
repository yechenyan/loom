# Workspaces

A Loom workspace is a named collection of generated cards, summaries, scan
state, and raw-file mappings. Use one workspace for one topic or project slice,
such as `energy`, `finance`, or `germany_energy`.

## Project Layout

`loomcli init` prepares this layout at the project root:

```text
loom/
  <workspace>/
  .loom/
raw_data/
```

Common paths:

- `raw_data/`: default place to keep local source data.
- `raw_data/<workspace>`: conventional source directory for one workspace.
- `loom/<workspace>`: generated Loom cards, summaries, profiles, and manifests.
- `loom/.loom/raw/<workspace>`: local cache for exact raw files.
- `loom/.loom/state/`: scan, sync, and recent-workspace state.

Loom can scan any local directory. The source does not have to live under
`raw_data/`.

## Workspace Names

Workspace names appear in commands and paths:

```bash
loomcli scan-index raw_data/energy to energy
loomcli status energy
loomcli get energy/path/to/file.csv
```

If a scan does not include `to <workspace>`, Loom reuses the recent workspace or
falls back to `demo`.

## Dataset Roots

Any scanned directory that contains `loom.md` is a dataset root. During a scan,
Loom currently processes each dataset's `loom.md` and `*.csv` files.

Each dataset writes:

- `overview.md`: human-readable dataset summary.
- `profile.json`: structured dataset profile.
- `<file>.card.md`: card for one CSV file.
- `<file>.profile.json`: structured CSV profile.

Nested dataset roots keep their directory layout under `loom/<workspace>/`.
Parent datasets list child dataset overviews and exclude CSV files that belong
to child datasets.

## Source Paths and Generated Paths

When the scan source is itself a dataset root, Loom writes that dataset under
`loom/<workspace>/<source-dir-name>/`. This keeps the workspace from flattening
root-level dataset files directly into `loom/<workspace>/`.

One workspace can track multiple source paths. Scanning the same dataset path
twice in one workspace stops with an error so the workspace does not contain
duplicate dataset entries.
