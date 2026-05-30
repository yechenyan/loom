from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


SUPPORTED_AGENTS = ("codex", "claude", "cursor", "copilot")


@dataclass(frozen=True)
class InstalledSkill:
    agent: str
    path: Path


def install_skills(codex_home: Path, workspace_root: Path, agents: tuple[str, ...] | None = None) -> tuple[InstalledSkill, ...]:
    selected_agents = agents or SUPPORTED_AGENTS
    installed: list[InstalledSkill] = []
    cli_launcher = workspace_root / "scripts" / "loomcli.py"
    skill_markdown = render_skill_markdown(workspace_root, cli_launcher)

    for agent in selected_agents:
        for skill_dir in get_skill_dirs(agent, codex_home, workspace_root):
            skill_dir.mkdir(parents=True, exist_ok=True)
            (skill_dir / "SKILL.md").write_text(skill_markdown, encoding="utf-8")
            installed.append(InstalledSkill(agent=agent, path=skill_dir))

    return tuple(installed)


def get_skill_dirs(agent: str, codex_home: Path, workspace_root: Path) -> tuple[Path, ...]:
    if agent == "codex":
        return (
            codex_home / "skills" / "loom-data",
            workspace_root / ".agents" / "skills" / "loom-data",
        )
    if agent == "claude":
        return (workspace_root / ".claude" / "skills" / "loom-data",)
    if agent == "cursor":
        return (workspace_root / ".cursor" / "skills" / "loom-data",)
    if agent == "copilot":
        return (workspace_root / ".copilot" / "skills" / "loom-data",)
    raise ValueError(f"Unsupported agent: {agent}")


def render_skill_markdown(workspace_root: Path, cli_launcher: Path) -> str:
    return f"""---
name: loom-data
description: Use the local Loom CLI and Python package whenever the user is asking data-related questions, needs to inspect local datasets, or wants to scan raw data into searchable cards.
---

# loom-data

Use this skill whenever the user's request is about data: answering data questions, tracing a metric back to source files, scanning local datasets, checking CSV contents, or fetching raw files on demand.

If the request sounds data-related, assume Loom should be the first tool you reach for.

In this repository, read `docs/reference/loom-reference.md` first if you need the canonical written description of Loom behavior.

## Names

- `loom ...` means a user-facing chat instruction.
- `loomcli ...` means the executable command a human or agent may run.
- `import loom` is still the Python package import.

Loom is designed for large local datasets:

1. Keep raw source files in any local directory you want to scan.
2. Scan them into compact cards under `loom/<workspace>`.
3. Let agents search summaries first.
4. Download raw files only when they are actually needed.

## Workspace layout

- Source data: `raw_data/<workspace>` by default, or any directory that contains `loom.md` and CSV files
- Generated cards: `loom/<workspace>`
- Local raw cache: `loom/.loom/raw/<workspace>`

## Default lookup workflow

For data questions, default to Loom even if the user did not explicitly mention `loom ask`.

When helping a user install Loom in a project, prefer the fast init path:

- `uv run loomcli init --agent codex`
- `uv run loomcli init --agent claude`
- `uv run loomcli init --agent cursor`

When `--agent` is present, Loom skips the interactive setup and installs the tutorial dataset automatically.
After init finishes, explicitly tell the user which `loom ...` examples belong in chat and which `uv run loomcli ...` examples belong in the terminal.

When the user writes `loom scan ...` in chat, treat it as a chat request, not a shell command.
Run `loomcli scan-index <path> [to <workspace>]` to generate the first pass of cards, then continue reading and improving the cards in chat before replying.

After `loomcli scan-index` finishes, do a real review before saying the scan is ready:

1. Read each scanned dataset's `loom.md`.
2. Read the generated `overview.md` and review every CSV card for small datasets, or at least one representative card per CSV family for larger datasets.
3. Check that the overview and cards explain the dataset purpose, key dimensions, scenario or year fields, units, and what each column is for.
4. If the generated summary is generic or misses source context from `loom.md`, rewrite or supplement it before replying.
5. Say explicitly whether you completed a full review or only a spot check.
6. Do not suggest `loomcli confirm` unless the review is complete or the user explicitly accepts a draft scan.

If the user writes `loom ask <question>` or `loom <question>`, do not run a lookup script for them.
Treat that as a request to inspect `./loom` first, then fetch exact raw files with `loomcli get` only when needed.

Only suggest `loomcli ...` commands when the user explicitly wants terminal commands or when an operational step like `confirm` or `push` truly belongs in the terminal.

When the user asks for a value inside a dataset, use this path by default:

1. Read `loom/` first.
2. Search the generated cards and summaries only long enough to identify the exact raw file path.
3. Run `loomcli get <workspace/path/to/file>` immediately, or use `loom.get("workspace/path/to/file")` in Python.
4. Search or parse the fetched local file to answer the question.

If the user asks any plain-language data question in chat, you should still think in the same Loom-first workflow:

1. Inspect `loom/` first.
2. Use cards and summaries to locate the likely dataset.
3. Fetch only the exact raw file you need.
4. Answer from the raw data you retrieved.

Do not spend turns rediscovering how Loom fetch works by reading `README.md`, `pyproject.toml`, or launcher scripts unless `loomcli get` actually fails.

Example lookup:

- User asks: `查找 OCGT 成本`
- First fetch: `loomcli get energy2/technology-data/costs_2035.csv`
- Then inspect the fetched CSV for `OCGT`

Example:

- `loomcli get energy/technology-data/costs.csv`

```python
import loom

local_path = loom.get("energy/technology-data/costs.csv")
```

`loom.get(...)` prefers local cache and fetches only the file you ask for.

## Chat examples

- `loom scan raw_data/energy`
- `loom scan raw_data/energy to energy`
- `loom ask OCGT 的成本是多少`
- `loom OCGT 的成本是多少`

## Terminal commands

- Confirm one workspace: `loomcli confirm energy`
- Confirm all pending explore changes: `loomcli confirm`
- Push one workspace: `loomcli push energy`
- Pull one workspace: `loomcli pull energy`
- Pull raw files for one workspace: `loomcli pull-raw energy`
- Set the default API endpoint: `loomcli set-api https://loom-api-free.onrender.com`

If you need workspace-root-aware launchers inside this repository, use:

- `uv run python {cli_launcher} scan-index raw_data/energy to energy --workspace-root {workspace_root}`
- `uv run python {cli_launcher} confirm <workspace> --workspace-root {workspace_root}`
- `uv run python {cli_launcher} status [workspace] --workspace-root {workspace_root}`
- `uv run python {cli_launcher} get workspace/path/to/file --workspace-root {workspace_root}`
- `uv run python {cli_launcher} push [workspace] --workspace-root {workspace_root}`

## Notes

- In this repository, `docs/reference/loom-reference.md` is the canonical written reference for Loom behavior.
- `loom-data` is the package name.
- `loom` is the chat trigger phrase.
- `loomcli` is the CLI command.
- `import loom` is the Python API.
- `loom scan` in chat should lead the agent to run `loomcli scan-index`, then continue curating the results in chat.
- `loomcli init` creates `./loom/` and `./raw_data/` at the current project root.
"""
