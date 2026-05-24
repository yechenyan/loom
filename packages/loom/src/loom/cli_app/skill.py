from __future__ import annotations

from pathlib import Path


def install_skill(codex_home: Path, workspace_root: Path) -> Path:
    skill_dir = codex_home / "skills" / "loom-scan"
    skill_dir.mkdir(parents=True, exist_ok=True)
    launcher = workspace_root / "scripts" / "loom.py"
    (skill_dir / "SKILL.md").write_text(render_skill_markdown(workspace_root, launcher), encoding="utf-8")
    return skill_dir


def render_skill_markdown(workspace_root: Path, launcher: Path) -> str:
    return f"""# loom-scan

Use this skill when the user types a Loom request in chat, especially commands like `loom scan energy` or `loom confirm energy`.

## Purpose

- Provide a fast path for Loom scan requests without doing broad repo exploration first.
- Generate dataset summaries under `test-project/loom/loom_explore/<topic>`.
- Track confirmed loom_explore changes in a dedicated git repository.
- Route sync commands like `loom push energy` and `loom pull energy` into the local CLI fast path.
- Prefer reading `loom_explore` outputs after the scan instead of reading raw CSV files directly.

## Fast Path

1. Do not browse unrelated files first.
2. Do not read anything under `wiki/discard`.
3. Run `uv run python {launcher} route "loom scan <topic>" --workspace-root {workspace_root}`.
4. Or run `uv run python {launcher} scan <topic> --workspace-root {workspace_root}`.
"""
