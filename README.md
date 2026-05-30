# loom-data

`loom-data` helps agents work with large local datasets without reading every raw CSV up front.

The workflow is:

1. Keep raw source data under `raw_data/<workspace>` or any directory that contains `loom.md`.
2. Scan that source into compact cards under `loom/<workspace>`.
3. Let the agent read `loom/` first.
4. Fetch only the exact raw files that are needed.

## Naming

Loom now uses fixed names for each layer:

- `loom ...` is a chat instruction for the agent.
- `loomcli ...` is the public terminal CLI.
- `loomrun ...` is the internal helper command used by the agent.
- `import loom` is the Python package import.

## Install

Install `uv` first, then add the package:

```bash
uv add loom-data
```

Check the CLI:

```bash
uv run loomcli --help
```

## Initialize a project

Run this in the project root:

```bash
uv run loomcli init
```

This creates:

```text
loom/
  <workspace>/
  .loom/
raw_data/
  <workspace>/
```

`loomcli init` asks which assistant you use, which default workspace name you want, and whether to install the tutorial dataset.
It installs the Loom skill only for the assistant you choose.

## Chat workflow

These are chat messages for your agent, not shell commands:

```text
loom scan raw_data/energy to energy
loom ask OCGT 的成本是多少
loom OCGT 的成本是多少
```

Expected behavior:

1. `loom scan ...`
   The agent runs `loomrun scan ...` to generate the first pass of cards, then continues refining the cards in chat.
2. `loom ask ...` or `loom <问题>`
   The agent inspects `loom/` first, then uses `loomcli get` only if it needs a specific raw file.

If the request is data-related but does not mention Loom explicitly, the installed skill should still make the agent think of Loom first.

## Terminal workflow

Use explicit terminal commands when you want to operate Loom by hand:

```bash
uv run loomcli confirm energy
uv run loomcli push energy
uv run loomcli pull energy
uv run loomcli pull-raw energy
uv run loomcli get energy/technology-data/costs.csv
uv run loomcli set-api https://loom-api-free.onrender.com
```

Notes:

- `loomcli scan` does not exist anymore. Scanning belongs to chat plus `loomrun`.
- `loomcli ask` does not exist anymore. Questions belong to the agent's Loom-first lookup workflow.
- If you omit `to <workspace>` in a scan request, Loom reuses the most recent workspace or falls back to `temporary`.

## Internal helper

Agents and repository maintainers can use:

```bash
uv run loomrun scan raw_data/energy to energy
uv run loomrun route "loom scan raw_data/energy to energy"
```

`loomrun` is an implementation detail. It is useful for automation, testing, and repository maintenance, but it is not the primary user-facing interface.

## Python API

```python
import loom

local_path = loom.get("energy/technology-data/costs.csv")
print(local_path)
```

`loom.get(...)` reuses local cache when possible and only downloads the latest raw file when needed.

## Workspace rules

- One workspace can track multiple source directories.
- Dataset paths inside one workspace must stay unique.
- Scan state is incremental per workspace and per source path.
- Generated cards and manifests store source-relative raw paths, so moving the project does not force a rebuild of unchanged datasets.

## Web app

Explore data online at [https://loom-web.onrender.com](https://loom-web.onrender.com).

## Maintainers

This repo also includes the workspace skill `.agents/skills/loom-cli-release` for publishing new `loom-data` CLI releases with the repository release script.
