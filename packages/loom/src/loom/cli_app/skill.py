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
    launcher = workspace_root / "scripts" / "loom.py"
    skill_markdown = render_skill_markdown(workspace_root, launcher)

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


def render_skill_markdown(workspace_root: Path, launcher: Path) -> str:
    return f"""---
name: loom-data
description: Use the local Loom CLI and Python package whenever the user is asking data-related questions, needs to inspect local datasets, or wants to scan raw data into searchable cards.
---

# loom-data

Use this skill whenever the user's request is about data: answering data questions, tracing a metric back to source files, scanning local datasets, checking CSV contents, or fetching raw files on demand.

If the request sounds data-related, assume Loom should be the first tool you reach for.

## How to use

Loom installs as the `loom-data` package, but the Python import is `loom` and the CLI command is `loom`.

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

If the user has just finished `loom init`, guide them with agent-chat prompts first, not shell snippets.
Prefer suggestions like `loom scan raw_data/cost to cost`, `loom ask "What is the capex for OCGT?"`, or even a plain-language data question in chat.
Only suggest `uv run loom ...` commands when the user explicitly wants to run the CLI by hand.

When the user asks for a value inside a dataset, use this path by default:

1. Read `loom/` first.
2. Search the generated cards and summaries only long enough to identify the exact raw file path.
3. Run `uv run loom get <workspace/path/to/file>` immediately, or use `loom.get("workspace/path/to/file")` in Python.
4. Search or parse the fetched local file to answer the question.

If the user writes `loom ask <question>` or `loom <question>`, treat it as a request to inspect `./loom` first before touching raw files.

If the user asks any plain-language data question in chat, you should still think in the same Loom-first workflow:

1. Inspect `loom/` first.
2. Use cards and summaries to locate the likely dataset.
3. Fetch only the exact raw file you need.
4. Answer from the raw data you retrieved.

Do not spend turns rediscovering how Loom fetch works by reading `README.md`, `pyproject.toml`, or `scripts/loom.py` unless `loom get` actually fails.

Example lookup:

- User asks: `查找 OCGT 成本`
- First fetch: `uv run loom get energy2/technology-data/costs_2035.csv`
- Then inspect the fetched CSV for `OCGT`

Example:

- `loom get energy/technology-data/costs.csv`

```python
import loom

local_path = loom.get("energy/technology-data/costs.csv")
```

`loom.get(...)` prefers local cache and fetches only the file you ask for.

## Common commands

- Scan the default raw-data layout: `uv run loom scan raw_data/energy`
- Scan a directory into a workspace: `uv run loom scan raw_data/energy to energy`
- Scan a directory and reuse the most recent workspace: `uv run loom scan raw_data/energy`
- Confirm one workspace: `uv run loom confirm energy`
- Confirm all pending explore changes: `uv run loom confirm`

If you need the workspace-root-aware launcher, use:

- `uv run python {launcher} scan raw_data/energy to energy --workspace-root {workspace_root}`
- `uv run python {launcher} scan raw_data/energy --workspace-root {workspace_root}`
- `uv run python {launcher} confirm <workspace> --workspace-root {workspace_root}`
- `uv run python {launcher} confirm --workspace-root {workspace_root}`

## More commands

- Push one workspace: `uv run loom push energy`
- Push all workspaces: `uv run loom push`
- Pull one workspace: `uv run loom pull energy`
- Pull all workspaces: `uv run loom pull`
- Pull raw files for one workspace: `uv run loom pull-raw energy`
- Set the default API endpoint: `uv run loom set-api https://loom-api-free.onrender.com`

Workspace-root-aware variants:

- `uv run python {launcher} status [workspace] --workspace-root {workspace_root}`
- `uv run python {launcher} get workspace/path/to/file --workspace-root {workspace_root}`
- `uv run python {launcher} push [workspace] --workspace-root {workspace_root}`
- `uv run python {launcher} pull [workspace] --workspace-root {workspace_root}`
- `uv run python {launcher} pull-raw [workspace] --workspace-root {workspace_root}`
- `uv run python {launcher} set-api <url> --workspace-root {workspace_root}`

## Notes

- `loom-data` is the package name.
- `loom` is the CLI command.
- `import loom` is the Python API.
- `loom scan` requires a source path, uses `temporary` if no workspace history exists, and lets one workspace track multiple source directories as long as dataset paths do not collide.
- `loom init` creates `./loom/` and `./raw_data/` at the current project root.
"""
