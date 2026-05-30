# Quickstart

This guide is for end users who want to use Loom with an agent.

For canonical behavior and naming, see `docs/reference/loom-reference.md`.

## Install

Install the package, then check the CLI:

```bash
uv add loom-data
uv run loomcli --help
```

## Initialize

Recommended fast path:

```bash
uv run loomcli init --agent codex
```

This installs focused agent skills for local data lookup, dataset scan review, and workspace operations.

Interactive setup:

```bash
uv run loomcli init
```

## Use Loom in Chat

These belong in agent chat, not the shell:

```text
loom scan raw_data/energy to energy
loom ask OCGT 的成本是多少
loom OCGT 的成本是多少
loom confirm energy
```

## Use Loom in the Terminal

These belong in the terminal:

```bash
uv run loomcli scan-index raw_data/energy to energy
uv run loomcli status energy
uv run loomcli confirm energy
uv run loomcli push energy
uv run loomcli pull energy
uv run loomcli get energy/technology-data/costs.csv
```

## Default Mental Model

1. Put raw data under `raw_data/<workspace>` or any directory you want to scan.
2. Ask the agent to scan with `loom scan ...`.
3. Let the agent read `loom/` first.
4. Fetch exact raw files only when needed.

Agents can also choose Loom automatically during modeling, coding, documentation, or paper writing when they need project-local, source-backed dataset facts.
