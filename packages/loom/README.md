# loom-data

`loom-data` publishes the `loom` Python package together with the `loomcli` console command.

## Install

Install Loom so `loomcli` runs directly in your terminal. The setup is complete
only after `loomcli --help` works without `uv run`.

Recommended:

```bash
pipx install loom-data
loomcli --help
```

With uv:

```bash
uv tool install loom-data
loomcli --help
```

With pip:

```bash
python -m pip install loom-data
loomcli --help
```

With conda:

```bash
conda create -n loom python=3.12
conda activate loom
python -m pip install loom-data
loomcli --help
```

## Initialize a project

Recommended fast path for AI-assisted onboarding:

```bash
loomcli init --agent codex
```

Interactive setup:

```bash
loomcli init
```

Both forms create or reuse:

```text
loom/
  <workspace>/
  .loom/
raw_data/
```

Fast init downloads the tutorial dataset into `raw_data/demo_germany_energy_data`.
The tutorial data is versioned outside the PyPI package and verified during
download. Use `--no-tutorial` to skip it or `--tutorial-url <url>` with
`--tutorial-sha256 <sha256>` to use a mirror. Fast init installs three focused agent skills: `loom-ask`,
`loom-scan`, and `loom-workspace-ops`.

## Recommended workflow

1. Put source data into any directory with `loom.md` and CSV files.
2. Ask the agent to scan it in chat with `/loom-scan <path> [to <workspace>]`.
3. Let the agent read `loom/` before touching raw files.
4. Use `loomcli get <workspace/path/to/file>` only for exact raw files that are needed.
   Raw paths preserve dataset directory structure, including the source-root
   dataset name when the scan source is itself a dataset root.
5. Use `loomcli confirm`, `loomcli push`, and `loomcli pull` for explicit terminal operations.

## Chat examples

```text
/loom-scan raw_data
/loom-ask build a 24-hour German electricity data html demo
loom 德国 2015 年有哪些发电装机容量数据？
```

`/loom-scan` or `loom scan` should lead the agent to run `loomcli scan-index` and then continue curating cards in chat.
During a scan, any directory containing `loom.md` is treated as a dataset root. Each dataset gets an `overview.md` and `profile.json`, and each CSV gets its own `.card.md` and `.profile.json`. Parent datasets preserve nested child dataset directories, exclude child CSV files from their own cards, and list direct child overview links. Rescans reuse unchanged CSV hashes and profiles so only changed datasets are rebuilt.
`/loom-ask`, `loom ask`, and bare `loom <问题>` should lead the agent to inspect `loom/` first rather than run a question-answering script.
Agents may also inspect Loom without an explicit `loom` prefix when another task needs project-local, source-backed dataset facts.

## CLI examples

```bash
loomcli scan-index raw_data/energy to energy
loomcli confirm energy
loomcli push energy
loomcli pull energy
loomcli pull-raw energy
loomcli get energy/demo_germany_energy_data/open_power_system_data/generation_capacity/germany_2015_net_capacity.csv
loomcli set-api https://loom-api-free.onrender.com
```

## Python API

```python
import loom

local_path = loom.get("energy/demo_germany_energy_data/open_power_system_data/generation_capacity/germany_2015_net_capacity.csv")
print(local_path)
```

`loom.get(...)` prefers local cache and fetches only the file you ask for.

## Notes

- `docs/reference/loom-reference.md` is the repository's canonical behavior reference.
- `loom-data` is the package name.
- `loomcli` is the public CLI command.
- `import loom` is the Python API.
- Use `loomcli scan-index` both for explicit terminal scans and for the agent's internal scan path.
