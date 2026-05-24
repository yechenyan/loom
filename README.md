# loom-data

`loom-data` turns large raw datasets into lightweight data cards so agents can search summaries first and download raw files only when needed.

The basic idea is simple:

1. Raw source data is often too large for an AI agent to inspect directly without wasting time and tokens.
2. Loom scans that raw data into compact cards and summaries under `loom/loom_explore`.
3. Agents read those cards first, then fetch only the exact raw files they need.

## How to use

Loom installs as the `loom-data` package, but the Python import is `loom` and the CLI command is `loom`.

## 1. Install `uv`

Recommended:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Other install options are available in the [uv docs](https://docs.astral.sh/uv/).

## 2. Install `loom-data`

```bash
uv add loom-data
```

If you want to use the CLI through the current project environment:

```bash
uv run loom --help
```

## 3. Initialize Loom in your project

Run this in the project root:

```bash
uv run loom install
```

This now initializes Loom in `./loom/`.

It also installs helper skill files for supported agents:

- Codex (`$CODEX_HOME/skills/loom-data` and workspace `.agents/skills/loom-data`)
- Claude
- Cursor
- Copilot

Installed workspace layout:

```text
loom/
  loom_raw/
  loom_explore/
  .loom/
```

## 4. Add raw data

Put your source files into:

```text
loom/loom_raw/<workspace>/
```

Example:

```text
loom/loom_raw/energy/loom.md
loom/loom_raw/energy/costs.csv

```

You can copy files there manually.

## 5. Generate data cards


You can  scan from chat with commands like:

```text
loom scan 
loom scan <workspace>
loom scan energy
```


Or bash:

```bash
uv run loom scan
uv run loom scan <workspace>
uv run loom scan energy
```




## 6. Confirm scan results

Optional, but recommended after you review the generated summaries.

run in chat:
```
loom confirm
loom confirm <workspace>
```

```bash
uv run loom confirm
```

or run in bash:
```bash
uv run loom confirm
uv run loom confirm <workspace>
```


## 7. Find data

Recommended workflow for agents:

1. Read `loom/loom_explore` first.
2. Search the generated cards and summaries.
3. Decide which exact raw file is needed.
4. Fetch that file on demand, for example `loom get energy/technology-data/costs.csv`.

## 8. Use raw data in Python

```python
import loom

local_path = loom.get("energy/technology-data/costs.csv")
print(local_path)
```

`loom.get(...)` reuses local cache when possible and only downloads the latest raw file when needed.

## More commands

Push one workspace:

```bash
uv run loom push energy
```

Push all workspaces:

```bash
uv run loom push
```

Pull one workspace:

```bash
uv run loom pull energy
```

Pull all workspaces:

```bash
uv run loom pull
```

Pull raw files for one workspace:

```bash
uv run loom pull-raw energy
```

Set the default API endpoint for future CLI usage:

```bash
uv run loom set-api https://loom-api-free.onrender.com
```

Online explore UI:

- [https://loom-web.onrender.com](https://loom-web.onrender.com)

## Notes

- `loom-data` is the package name.
- `loom` is the CLI command.
- `import loom` is the Python API.
- `loom scan` now works with or without a workspace name.
- `loom install` now creates `./loom/` at the current project root.
- `loom install` also prepares reusable agent skill files so other users can work with the same Loom workflow faster.
