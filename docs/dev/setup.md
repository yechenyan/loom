# Developer Setup

This guide is for contributors working in this repository.

## Package and CLI

- Package name: `loom-data`
- Python import: `import loom`
- CLI entrypoint: `loomcli`
- Repository launcher: `scripts/loomcli.py`

## Basic Checks

```bash
uv run python scripts/loomcli.py --help
uv run loomcli --help
```

## Repository Areas

- `packages/loom/`
  Main client package and CLI
- `packages/loom-server/`
  Server package
- `scripts/`
  Local helper entrypoints
- `docs/`
  Current documentation
- `tasks/`
  Active task notes
- `tasks/history/`
  Completed task notes

## Before Changing Behavior

1. Check the code first.
2. Update `docs/reference/loom-reference.md` before derivative docs.
3. Update any affected skill templates if the agent workflow changed.
