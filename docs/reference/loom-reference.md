# Loom Reference

This document is the written source of truth for Loom naming, behavior, and workflows in this repository.

If any other document disagrees with the code, trust the code and update this file first.

## Naming

- `loom ...`: chat instruction sent to an agent
- `loomcli ...`: executable CLI command used by humans and agents
- `import loom`: Python package import path
- `loom-data`: published package name

Do not mix these layers.

## Documentation Roles

- `README.md`: repository landing page and navigation
- `docs/reference/loom-reference.md`: canonical Loom behavior and terminology
- `docs/user/`: end-user guides derived from this file
- `docs/dev/`: developer and maintainer guides derived from this file and the code
- `tasks/`: active task notes
- `tasks/history/`: completed task notes and history

## CLI Commands

The public CLI entrypoint is `loomcli`.

Commands currently defined in `packages/loom/src/loom/cli_app/parser.py`:

- `init`
- `scan-index`
- `set-api`
- `get`
- `status`
- `confirm`
- `push`
- `pull`
- `pull-raw`
- `server-init-db`
- `server-run`

## Chat Semantics

`packages/loom/src/loom/chat.py` currently recognizes:

- `loom scan <path> [to <workspace>]`
- `/loom-scan <path> [to <workspace>]`
- `scan <path> with loom`
- `loom ask <question>`
- `/loom-ask <question>`
- `loom <question>`
- `loom confirm [workspace]`
- `loom push [workspace]`
- `loom pull [workspace]`
- `loom status [workspace]`

Rules:

- `loom scan ...` is a chat intent, not a shell command.
- `/loom-scan ...` is a slash-style alias for `loom scan ...`.
- `loom ask ...` and bare `loom <question>` are lookup intents, not a separate CLI QA command.
- `/loom-ask ...` is a slash-style alias for `loom ask ...`.
- `loom install ...` and `loomcli install ...` are not supported.
- `loom get ...`, `loom init ...`, and `loom set-api ...` are not valid chat forms.

## Workspace Layout

`loomcli init` prepares these paths at the workspace root:

```text
loom/
  <workspace>/
  .loom/
raw_data/
```

Common roles:

- `raw_data/`: local source-data root by default
- `raw_data/<workspace>`: conventional place to keep one workspace's source data
- `loom/<workspace>`: generated Loom cards and summaries
- `loom/.loom/raw/<workspace>`: local raw-file cache

Loom can also scan any local source directory, not only `raw_data/<workspace>`.

## Initialization

Loom should be installed so `loomcli` is directly available in the terminal.
Do not require users or agents to run CLI commands through `uv run`.

Recommended tool install:

```bash
pipx install loom-data
loomcli --help
```

Alternative installs:

```bash
uv tool install loom-data
loomcli --help
```

```bash
python -m pip install loom-data
loomcli --help
```

```bash
conda create -n loom python=3.12
conda activate loom
python -m pip install loom-data
loomcli --help
```

If `loomcli --help` fails after installation, fix the environment `PATH`,
activate the intended environment, or reinstall with a tool installer such as
`pipx` or `uv tool install`. `python -m loom ...` is a fallback for diagnosing
the active Python environment, not the primary documented workflow.

Interactive setup:

```bash
loomcli init
```

Fast path for AI onboarding:

```bash
loomcli init --agent codex
```

Current `--agent` behavior from `packages/loom/src/loom/cli_app/init_flow.py`:

- skips the interactive setup
- installs the selected agent's Loom skills
- creates or reuses `./loom` and `./raw_data`
- creates `./loom/<default-workspace>`
- saves the default workspace as `demo`
- downloads tutorial data into `raw_data/demo_germany_energy_data`
- prints chat examples and terminal examples separately

Tutorial data is not packaged inside the `loom-data` PyPI distribution. The
CLI downloads a versioned tarball, verifies its SHA256 when configured, and
unpacks it into `raw_data/demo_germany_energy_data`. Tutorial download failure
does not fail workspace initialization.

Tutorial options:

- `--no-tutorial`: skip tutorial data download
- `--tutorial-url <url>`: override the tutorial archive URL; requires `--tutorial-sha256`
- `--tutorial-sha256 <sha256>`: override the expected archive SHA256
- `--force-tutorial`: replace an existing tutorial directory

Supported agent values:

- `codex`
- `claude`
- `cursor`
- `copilot`

Installed agent skills:

- `loom-ask`: local dataset fact lookup from cards and exact raw files
- `loom-scan`: scan local datasets, then review and curate generated cards
- `loom-workspace-ops`: init, status, confirm, push, pull, pull-raw, set-api, and chat-vs-CLI help

## Scan Workflow

Chat form:

```text
loom scan raw_data/energy to energy
/loom-scan raw_data/energy to energy
```

CLI form:

```bash
loomcli scan-index raw_data/energy to energy
```

Rules from the current implementation:

- the source path is required
- `to <workspace>` is optional
- if no workspace is provided, Loom reuses the recent workspace or falls back to `demo`
- any directory containing `loom.md` is a dataset root
- each dataset writes an `overview.md` and `profile.json`
- each CSV file writes its own `.card.md` and `.profile.json`
- parent datasets keep their nested dataset directory layout in `loom/<workspace>/`
- a parent dataset excludes CSV files that belong to a nested child dataset
- a parent dataset overview lists direct child dataset overviews
- each dataset currently processes `loom.md` and `*.csv` files only
- rescans reuse unchanged CSV hashes and profiles, then rebuild only changed datasets
- one workspace can track multiple source paths
- duplicate dataset paths stop the scan with an error
- if a source root is itself a dataset root, Loom writes that dataset under `loom/<workspace>/<source-dir-name>/` instead of flattening files into `loom/<workspace>/`

Expected agent behavior:

1. Run `loomcli scan-index ...` for the first pass.
2. Review the generated cards and summaries.
3. Read the source `loom.md` for each scanned dataset.
4. Fix or supplement generic summaries before calling the scan ready.
5. Suggest `loomcli confirm` only after the review is complete, unless the user explicitly accepts a draft.

## Query Workflow

Chat forms:

```text
loom ask "What German wind and solar data is available?"
/loom-ask "What German wind and solar data is available?"
loom 德国 2015 年有哪些发电装机容量数据？
```

Expected agent behavior:

1. Inspect `loom/` first.
2. Use cards and summaries to locate the likely dataset.
3. Fetch only the exact raw file needed with `loomcli get <workspace/path/to/file>`.
4. Answer from the fetched local raw file.

Agents should also choose this workflow without an explicit `loom` prefix when data analysis, modeling, visualization, reporting, coding, documentation, or paper writing depends on project-local, source-backed dataset facts, such as model parameters, units, assumptions, costs, CSV contents, or provenance. Inspect `loom/` cards and summaries before reading `raw_data` directly, then fetch only exact raw files with `loomcli get` or `loom.get(...)`. Do not use Loom for ordinary data-processing code with no local source-data lookup, general concept explanations, or external live data unless the user asks.

`loomcli ask` does not exist and should not be documented.

## Sync Workflow

Terminal commands:

```bash
loomcli status energy
loomcli confirm energy
loomcli push energy
loomcli pull energy
loomcli pull-raw energy
```

Chat intents such as `loom confirm energy` and `loom push energy` may be interpreted by an agent as instructions to run the matching CLI commands.

## Python API

```python
import loom

local_path = loom.get("energy/demo_germany_energy_data/open_power_system_data/generation_capacity/germany_2015_net_capacity.csv")
```

Current exports in `packages/loom/src/loom/__init__.py` include `get`, `pull`, `scan_path_to_explore`, `scan_topic_from_chat`, chat parsing helpers, and base URL helpers.

## Maintenance Rule

When Loom behavior, naming, or workflow changes, update this file before any derivative documentation.
