# loom-data

`loom-data` publishes the `loom` Python package together with the `loomcli` console command.

## Install

```bash
uv add loom-data
uv run loomcli --help
```

## Initialize a project

Recommended fast path for AI-assisted onboarding:

```bash
uv run loomcli init --agent codex
```

Interactive setup:

```bash
uv run loomcli init
```

Both forms create or reuse:

```text
loom/
  <workspace>/
  .loom/
raw_data/
```

Fast init also installs the tutorial dataset under `raw_data/cost`.

## Recommended workflow

1. Put source data into any directory with `loom.md` and CSV files.
2. Ask the agent to scan it in chat with `loom scan <path> [to <workspace>]`.
3. Let the agent read `loom/` before touching raw files.
4. Use `loomcli get <workspace/path/to/file>` only for exact raw files that are needed.
5. Use `loomcli confirm`, `loomcli push`, and `loomcli pull` for explicit terminal operations.

## Chat examples

```text
loom scan raw_data/energy to energy
loom ask OCGT 的成本是多少
loom OCGT 的成本是多少
```

`loom scan` should lead the agent to run `loomcli scan-index` and then continue curating cards in chat.
`loom ask` and bare `loom <问题>` should lead the agent to inspect `loom/` first rather than run a question-answering script.

## CLI examples

```bash
uv run loomcli scan-index raw_data/energy to energy
uv run loomcli confirm energy
uv run loomcli push energy
uv run loomcli pull energy
uv run loomcli pull-raw energy
uv run loomcli get energy/technology-data/costs.csv
uv run loomcli set-api https://loom-api-free.onrender.com
```

## Python API

```python
import loom

local_path = loom.get("energy/technology-data/costs.csv")
print(local_path)
```

`loom.get(...)` prefers local cache and fetches only the file you ask for.

## Notes

- `docs/reference/loom-reference.md` is the repository's canonical behavior reference.
- `loom-data` is the package name.
- `loomcli` is the public CLI command.
- `import loom` is the Python API.
- Use `loomcli scan-index` both for explicit terminal scans and for the agent's internal scan path.
