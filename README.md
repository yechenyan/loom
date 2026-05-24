# loom workspace

This repository is configured as a `uv` workspace.

## Quick start

```bash
uv sync
```

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

## Workspace layout

- Root workspace config: `pyproject.toml`
- Package member: `test-project/loom`
