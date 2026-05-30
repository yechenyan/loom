from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path


SUPPORTED_AGENTS = ("codex", "claude", "cursor", "copilot")
SKILL_TEMPLATES = {
    "loom-local-data-lookup": "loom_local_data_lookup_skill.md",
    "loom-dataset-scan-review": "loom_dataset_scan_review_skill.md",
    "loom-workspace-ops": "loom_workspace_ops_skill.md",
}


@dataclass(frozen=True)
class InstalledSkill:
    agent: str
    path: Path


def install_skills(codex_home: Path, workspace_root: Path, agents: tuple[str, ...] | None = None) -> tuple[InstalledSkill, ...]:
    selected_agents = agents or SUPPORTED_AGENTS
    installed: list[InstalledSkill] = []
    rendered_skills = {
        skill_name: render_skill_markdown(template_name)
        for skill_name, template_name in SKILL_TEMPLATES.items()
    }

    for agent in selected_agents:
        for skill_name, skill_markdown in rendered_skills.items():
            for skill_dir in get_skill_dirs(agent, codex_home, workspace_root, skill_name):
                skill_dir.mkdir(parents=True, exist_ok=True)
                (skill_dir / "SKILL.md").write_text(skill_markdown, encoding="utf-8")
                installed.append(InstalledSkill(agent=agent, path=skill_dir))

    return tuple(installed)


def get_skill_dirs(agent: str, codex_home: Path, workspace_root: Path, skill_name: str) -> tuple[Path, ...]:
    if agent == "codex":
        return (
            codex_home / "skills" / skill_name,
            workspace_root / ".agents" / "skills" / skill_name,
        )
    if agent == "claude":
        return (workspace_root / ".claude" / "skills" / skill_name,)
    if agent == "cursor":
        return (workspace_root / ".cursor" / "skills" / skill_name,)
    if agent == "copilot":
        return (workspace_root / ".copilot" / "skills" / skill_name,)
    raise ValueError(f"Unsupported agent: {agent}")


def render_skill_markdown(template_name: str) -> str:
    return files("loom.cli_app").joinpath("templates", template_name).read_text(encoding="utf-8")
