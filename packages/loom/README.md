# loom-data

`loom-data` publishes the `loom` Python package together with the `loomcli` and `loomrun` console commands.

## Naming

- `loom ...` is the chat form used with an AI agent.
- `loomcli ...` is the public terminal CLI.
- `loomrun ...` is the internal helper command used by agents and repository tooling.
- `import loom` remains the Python import path.

## Install

```bash
uv add loom-data
uv run loomcli --help
```

## Initialize a project

```bash
uv run loomcli init
```

This prepares:

```text
loom/
  <workspace>/
  .loom/
raw_data/
  <workspace>/
```

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

`loom scan` should lead the agent to run `loomrun scan` and then continue curating cards in chat.
`loom ask` and bare `loom <问题>` should lead the agent to inspect `loom/` first rather than run a question-answering script.

## CLI examples

```bash
uv run loomcli confirm energy
uv run loomcli push energy
uv run loomcli pull energy
uv run loomcli pull-raw energy
uv run loomcli get energy/technology-data/costs.csv
uv run loomcli set-api https://loom-api-free.onrender.com
```

## Internal helper examples

```bash
uv run loomrun scan raw_data/energy to energy
uv run loomrun route "loom scan raw_data/energy to energy"
```

## Python API

```python
import loom

local_path = loom.get("energy/technology-data/costs.csv")
print(local_path)
```

`loom.get(...)` prefers local cache and fetches only the file you ask for.

## Notes

- `loom-data` is the package name.
- `loomcli` is the public CLI command.
- `loomrun` is the internal helper command.
- `import loom` is the Python API.
