# loom-data

`loom-data` publishes the `loom` Python package and the `loom` CLI.

It is used to:

- read raw Loom data with a local cache
- scan `loom_raw` datasets into summarized `loom_explore` outputs
- review and confirm local workspace changes
- push and pull workspaces against a Loom sync server

The install name is `loom-data`, but the Python import stays `import loom` and the command stays `loom`.

## What Loom does

Loom turns raw datasets under `test-project/loom/loom_raw` into structured summaries under `test-project/loom/loom_explore`.

This lets agents and people read generated overviews, profiles, and data cards first, instead of opening every raw CSV directly.

## Directory layout

Loom expects this workspace layout:

- `test-project/loom/loom_raw/<topic>`: raw source datasets
- `test-project/loom/loom_explore/<topic>`: generated scan output
- `test-project/loom/.loom/raw/<workspace>`: local raw cache

In this repository:

- client package source: `packages/loom/src/loom`
- server package source: `packages/loom-server/src/loom_server`

## Dataset rule

If a directory contains `loom.md`, Loom treats that directory as a dataset root.

That dataset includes CSV files under the directory and its children. If a nested child directory also has its own `loom.md`, it becomes a separate dataset and is not folded into the parent dataset scan.

## Install

Install from PyPI:

```bash
pip install loom-data
```

For local development in this repository:

```bash
uv sync
uv pip install -e .
```

If you also want the FastAPI sync server and `loom-server` CLI:

```bash
uv pip install -e packages/loom-server
```

## Initial setup

Run this once in a workspace to install the local Codex skill and initialize `loom_explore` as a separate git repository:

```bash
loom install
```

Or, if you want to be explicit:

```bash
loom install --workspace-root /path/to/workspace
```

This setup is what enables the scan workflow to show pending changes and later confirm them into the `loom_explore` git history.

## Python API

Read one raw file and make sure it exists in the local raw cache:

```python
import loom

local_path = loom.get("energy/technology-data/costs.csv")
print(local_path)
```

Refresh a workspace raw cache:

```python
import loom

loom.pull("energy")
```

Parse chat text into a Loom request:

```python
import loom

request = loom.parse_chat_request("loom scan energy")
print(request)
```

## CLI overview

Main commands:

```bash
loom install
loom scan <topic>
loom route "<message>"
loom get <workspace/path/to/file>
loom pull-raw [workspace]
loom status [workspace]
loom confirm [workspace]
loom push [workspace]
loom pull [workspace]
```

If `workspace` is omitted for `push`, `pull`, or `pull-raw`, Loom uses all available top-level workspaces where that behavior is supported.

## Scan a topic

Run a local scan:

```bash
loom scan energy
```

This scan is local Python logic only. It will:

- inspect `test-project/loom/loom_raw/energy`
- find dataset roots via `loom.md`
- read CSV files
- generate dataset summaries and cards
- write outputs to `test-project/loom/loom_explore/energy`
- print the resulting pending changes

You can also test whether a chat message would route into a Loom action:

```bash
loom route "loom scan energy"
```

## Review and confirm scan output

After a scan:

```bash
loom status energy
loom confirm energy
```

`loom status` shows pending files plus sync metadata.

`loom confirm` creates a commit inside the separate `loom_explore` git repository so the workspace has a local confirmed state before syncing.

## Read raw data

Use the CLI:

```bash
loom get energy/technology-data/costs.csv
```

Use the Python API:

```python
import loom

path = loom.get("energy/technology-data/costs.csv")
```

Lookup behavior:

- Loom first checks `test-project/loom/.loom/raw/...`
- if the file is already cached locally, that path is reused
- if a matching file already exists under `test-project/loom/loom_raw/...` or `.raw_data/...`, Loom links it into `.loom/raw`
- otherwise Loom fetches the latest version from the Loom sync server

Repeated reads reuse the local cache.

## Refresh raw cache

Refresh one workspace:

```bash
loom pull-raw energy --server-url http://127.0.0.1:8765
```

Or in Python:

```python
import loom

loom.pull("energy")
```

`loom pull-raw` and `loom.pull(...)` compare the remote raw manifest by `path + sha256` and only refresh changed or deleted files.

## Push and pull workspaces

Push one workspace:

```bash
loom push energy --server-url http://127.0.0.1:8765
```

Pull one workspace:

```bash
loom pull energy --server-url http://127.0.0.1:8765
```

Pull all workspaces:

```bash
loom pull --server-url http://127.0.0.1:8765
```

Current sync behavior is rebase-oriented:

- `push` auto-confirms pending local changes before sending
- if the remote has advanced, `push` rebases local confirmed work first, then continues
- `pull` fast-forwards when possible
- if local confirmed commits exist, `pull` rebases them on top of the latest remote revision
- rebase conflicts return a non-zero exit code and keep conflict markers in `loom_explore`

After resolving a conflict, run:

```bash
loom confirm <workspace>
loom push <workspace>
```

## Optional server commands

The published `loom-data` package focuses on client workflows. Server commands require the separate `loom-server` package.

Install it first:

```bash
pip install loom-server
```

Or in this repository:

```bash
uv pip install -e packages/loom-server
```

Then you can use:

```bash
loom server-init-db
loom server-run
```

Default server URL:

```text
http://127.0.0.1:8765
```

Default database URL:

```text
postgresql+psycopg2://loom@127.0.0.1:5432/loom
```

Initialize the server database:

```bash
loom server-init-db
```

Run the server:

```bash
loom server-run --storage-root /tmp/loom-server-storage
```

## Scan outputs

After scanning, Loom writes files such as:

- `README.md`: topic-level entry file
- `overview.md`: dataset overview
- `profile.json`: dataset-level machine-readable summary
- `*.card.md`: per-CSV data card
- `*.profile.json`: per-CSV machine-readable profile

## Release

Build distributions:

```bash
uv build
```

Upload to TestPyPI first:

```bash
uv publish --publish-url https://test.pypi.org/legacy/
```

Upload to PyPI:

```bash
uv publish
```
