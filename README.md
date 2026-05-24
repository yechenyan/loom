# loom workspace

This repository is configured as a `uv` workspace.

## Quick start

```bash
uv sync
```

Install the client package in editable mode if you want both the Python API and the `loom` CLI on your shell path:

```bash
uv pip install -e .
```

Install the service package separately when you want the FastAPI sync service and the `loom-server` CLI:

```bash
uv pip install -e packages/loom-server
```

Then you can use either form:

```python
import loom

path = loom.get("energy/technology-data/costs.csv")
```

```bash
loom get energy/technology-data/costs.csv
loom pull-raw energy
```

Raw cache and local Loom state now live under:

```text
test-project/loom/.loom/
```

Raw access behavior:

- `loom.get("workspace/path/to/file")` first checks `test-project/loom/.loom/raw/...`
- if the file is already available locally, Loom reuses it
- if a matching local raw source exists under `test-project/loom/loom_raw` or `.raw_data`, Loom links that file into `.loom/raw`
- otherwise Loom fetches only the missing latest file from the sync server
- `loom.pull(...)` and `loom pull-raw ...` compare the remote raw manifest by path and hash, then refresh only changed or deleted cache entries

## Install Loom Scan Fast Path

Run this once to install the local Codex skill for `loom scan <topic>` and initialize the `loom_explore` git repo:

```bash
uv run python scripts/loom.py install
```

After that, Codex can recognize chat inputs like `loom scan energy` faster and route them to the scan flow directly.

You can also run the scanner manually:

```bash
uv run python scripts/loom.py scan energy
```

After scanning, review changes and confirm them into the local `loom_explore` history:

```bash
uv run python scripts/loom.py status energy
uv run python scripts/loom.py confirm energy
```

## Sync Server

The sync server now lives in the separate `packages/loom-server` package. It uses FastAPI for the API layer and PostgreSQL for revision metadata.

By default, Loom expects a local PostgreSQL instance at:

```text
postgresql+psycopg2://loom@127.0.0.1:5432/loom
```

`loom-server init-db` and `loom-server run` will automatically create the `loom` database if the local PostgreSQL server is reachable and the database does not exist yet.

Initialize the server schema:

```bash
uv run python scripts/loom-server.py init-db
```

Run the server:

```bash
uv run python scripts/loom-server.py run --storage-root .loom-server-storage
```

Push and pull workspaces:

```bash
uv run python scripts/loom.py push energy --server-url http://127.0.0.1:8765
uv run python scripts/loom.py pull energy --server-url http://127.0.0.1:8765
uv run python scripts/loom.py pull-raw energy --server-url http://127.0.0.1:8765
```

Push and pull now use rebase-style workspace sync:

- `push` will auto-confirm local pending changes, pull the latest remote revision when needed, rebase local confirmed work onto it, then continue the incremental push
- `pull` will fast-forward when possible, or rebase local confirmed work onto the latest remote revision instead of blindly overwriting it
- if a rebase conflict happens, Loom keeps conflict markers in `loom_explore`, returns a non-zero exit code, and asks you to resolve the files, run `loom confirm <workspace>`, then `loom push <workspace>`
- normal `pull` / `push` raw refresh only updates files already present under `test-project/loom/.loom/raw/<workspace>/...`
- `pull-raw` and `loom.pull(...)` still support intentional full raw cache refresh for a workspace
- if local `test-project/loom/loom_raw/...` files disagree with the remote raw manifest, Loom will not overwrite them and will write `loom.raw-conflict.md` next to the nearest `loom.md`

## Web App

A React web app lives in [web/package.json](/Users/maxiao/Documents/code2/loom/web/package.json) and reads dataset summaries from the FastAPI server.

Install and run it with `pnpm`:

```bash
cd /Users/maxiao/Documents/code2/loom/web
pnpm install
pnpm dev --host 127.0.0.1
```

Then open:

```text
http://127.0.0.1:4173
```

The Vite dev server proxies `/api` requests to the Loom FastAPI server on `http://127.0.0.1:8765`.

## Workspace layout

- Root workspace config: `pyproject.toml`
- Client package source: `packages/loom/src/loom`
- Service package source: `packages/loom-server/src/loom_server`
