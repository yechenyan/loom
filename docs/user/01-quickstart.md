# Quickstart

This guide gets a new project ready for agent-assisted local data lookup.

## Install

Install Loom so `loomcli` runs directly in your terminal. Setup is complete only
after this command works without `uv run`:

```bash
loomcli --help
```

Recommended:

```bash
pipx install loom-data
loomcli --help
```

Other supported install paths:

```bash
uv tool install loom-data
python -m pip install loom-data
```

For conda:

```bash
conda create -n loom python=3.12
conda activate loom
python -m pip install loom-data
loomcli --help
```

If `loomcli --help` fails, fix `PATH`, activate the intended environment, or
reinstall with `pipx` or `uv tool install`.

## Initialize

For AI-assisted onboarding, run the fast path for your agent:

```bash
loomcli init --agent codex
```

Supported agent values are `codex`, `claude`, `cursor`, and `copilot`. Fast init
creates or reuses `./loom` and `./raw_data`, sets the default workspace to
`demo`, installs the tutorial data under `raw_data/demo_germany_energy_data`,
and installs Loom agent skills.

For an interactive setup:

```bash
loomcli init
```

## First Scan

Ask the agent in chat:

```text
loom scan raw_data/demo_germany_energy_data to germany_energy
```

Or run the terminal command directly:

```bash
loomcli scan-index raw_data/demo_germany_energy_data to germany_energy
```

Both forms build cards and profiles under `loom/germany_energy/`.

## First Question

Ask the agent:

```text
loom ask "What German wind and solar data is available?"
```

The agent should inspect `loom/` first, identify the relevant card, then fetch an
exact raw file only if the answer needs the underlying data.

## Save the Work

After the scan has been reviewed:

```bash
loomcli status germany_energy
loomcli confirm germany_energy
```

Use `confirm` after the generated cards look ready to keep.
