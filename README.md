# loom-data

`loom-data` turns large raw datasets into lightweight data cards so agents can search summaries first and download raw files only when needed.

The basic idea is simple:

1. Raw source data is often too large for an AI agent to inspect directly without wasting time and tokens.
2. Loom scans that raw data into compact cards and summaries under `loom/`.
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
uv run loom init
```

This initializes Loom in `./loom/` and asks a few short questions in English:

- which assistant you use
- the default workspace name
- whether to install the tutorial dataset

`loom init` installs the helper skill only for the assistant you choose:

- OpenAI Codex (`$CODEX_HOME/skills/loom-data` and workspace `.agents/skills/loom-data`)
- Claude (`.claude/skills/loom-data`)
- Cursor (`.cursor/skills/loom-data`)
- Copilot (`.copilot/skills/loom-data`)

If `./loom/` already exists, `loom init` shows a small menu instead of reinitializing everything. From there you can install another skill, choose a new default workspace, or read the reset/help text.

If you prefer to let an AI agent handle setup end-to-end, you can paste a prompt like this into ChatGPT / Claude / Cursor:

```text
Please set up Loom in this project for me: if `uv` is not installed, install it first and make sure the command is available; then run `uv add loom-data`; then run `uv run loom init` in the project root; during init choose the assistant I am using, keep the default workspace, skip the tutorial dataset, and tell me whether both `loom/` and `raw_data/` were created successfully.
```

Installed workspace layout:

```text
loom/
  <workspace>/
  .loom/
raw_data/
  <workspace>/
```

## 4. Add raw data

Put your source files into any directory that contains dataset folders with `loom.md` and CSV files.

Example:

```text
raw_data/energy/technology-data/loom.md
raw_data/energy/technology-data/costs.csv
```

The default local convention is `raw_data/<workspace>/...`, but `loom scan` still accepts any relative or absolute directory path.

## 5. Generate data cards


You can scan from chat with commands like:

```text
loom scan raw_data/energy
loom scan raw_data/energy to energy
loom scan /absolute/path/to/energy-source to energy
```

Or bash:

```bash
uv run loom scan raw_data/energy
uv run loom scan raw_data/energy to energy
uv run loom scan /absolute/path/to/energy-source to energy
```

Rules:

- `<path>` is required.
- `to <workspace>` is optional.
- If you omit `to <workspace>`, Loom reuses the most recently scanned or created workspace.
- If there is no recent workspace yet, Loom creates and uses `temporary`.
- If the target workspace does not exist yet, Loom creates it automatically.
- One workspace can track multiple scan source paths at the same time.
- If two source paths would generate the same dataset path inside one workspace, Loom stops and asks you to resolve the name conflict first.
- Scan state is incremental per workspace and per source path.
- Dataset cards and manifests store source-relative raw paths such as `technology-data` or `technology-data/costs.csv`, not machine-specific absolute paths.
- If you copy the project or move the workspace root, Loom reuses the same relative scan sources and avoids rebuilding unchanged datasets just because the absolute filesystem path changed.

For AI chat onboarding, the simplest path is:

```text
loom scan raw_data/cost to cost
loom ask OCGT 的成本是多少
loom OCGT 的成本是多少
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

1. Read `loom/` first.
2. Search the generated cards and summaries.
3. Decide which exact raw file is needed.
4. Fetch that file on demand, for example `loom get energy/technology-data/costs.csv`.

If the user writes `loom ask <question>` or `loom <question>`, treat that as a request to inspect `loom/` first.

`loom ask <question>` now runs a local lookup flow:

1. Search `loom/` for the most relevant workspace, dataset, and CSV card.
2. Fetch the matching raw file with `loom get` if it is not cached yet.
3. Print the best match, local raw file path, and matching rows.
4. Print `Likely answer` when one row is the obvious best hit.

You can use the same flow directly in the CLI:

```bash
uv run loom ask OCGT cost
uv run loom OCGT cost
```

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
- `loom scan` now requires a source path: `loom scan <path> [to <workspace>]`.
- `loom init` now creates `./loom/` and `./raw_data/` at the current project root.
- `loom init` installs one agent skill at a time instead of generating every supported agent skill by default.
