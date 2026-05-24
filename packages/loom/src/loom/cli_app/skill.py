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
description: Use the local Loom CLI and Python package to scan raw datasets into data cards, confirm explore changes, sync workspaces, and fetch raw files on demand.
---

# loom-data

Use this skill when the user needs to work with data stored in the local Loom workspace.

## Why Loom

- Raw datasets are often too large for an agent to inspect directly without wasting time and tokens.
- Loom first turns raw files into compact data cards under `loom/loom_explore`.
- Agents should search those cards first, then fetch only the specific raw files they need.

## Workspace layout

- Raw data: `loom/loom_raw/<workspace>`
- Generated cards: `loom/loom_explore/<workspace>`
- Local raw cache: `loom/.loom/raw/<workspace>`

## Fast path

1. Read `loom/loom_explore` first.
2. Search the generated cards and summaries before touching raw files.
3. Decide which exact raw file is needed.
4. Fetch that file on demand with `loom get workspace/path/to/file` or `loom.get("workspace/path/to/file")`.

Example:

- `loom get energy/technology-data/costs.csv`

```python
import loom

local_path = loom.get("energy/technology-data/costs.csv")
```

## Scan and confirm

1. To scan one workspace, run `uv run python {launcher} scan <workspace> --workspace-root {workspace_root}`.
2. To scan every workspace, run `uv run python {launcher} scan --workspace-root {workspace_root}`.
3. After reviewing changes, confirm them with `uv run python {launcher} confirm <workspace> --workspace-root {workspace_root}`.

## Useful commands

- `uv run python {launcher} status [workspace] --workspace-root {workspace_root}`
- `uv run python {launcher} get workspace/path/to/file --workspace-root {workspace_root}`
- `uv run python {launcher} push [workspace] --workspace-root {workspace_root}`
- `uv run python {launcher} pull [workspace] --workspace-root {workspace_root}`
- `uv run python {launcher} pull-raw [workspace] --workspace-root {workspace_root}`
"""
