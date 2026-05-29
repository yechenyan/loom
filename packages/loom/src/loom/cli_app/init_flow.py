from __future__ import annotations

import getpass
from pathlib import Path

from ..raw_cache_support import resolve_raw_data_root
from ..explore_repo import ensure_explore_repo
from ..scan_state import save_recent_workspace
from .skill import install_skills
from .tutorial_data import TUTORIAL_FILES


AGENT_LABELS = {
    "codex": "OpenAI Codex",
    "claude": "Claude",
    "cursor": "Cursor",
    "copilot": "Copilot",
}

MENU_ACTIONS = {
    "1": "delete",
    "2": "install-skill",
    "3": "create-workspace",
    "4": "help",
}


def run_init_flow(codex_home: Path, workspace_root: Path, agents: tuple[str, ...] | None = None) -> int:
    loom_root = workspace_root / "loom"
    if loom_root.exists():
        return _run_existing_workspace_menu(codex_home, workspace_root, agents)
    return _run_fresh_init(codex_home, workspace_root, agents)


def _run_fresh_init(codex_home: Path, workspace_root: Path, agents: tuple[str, ...] | None) -> int:
    selected_agents = agents or (_prompt_agent(),)
    workspace_name = _prompt_workspace_name()
    tutorial_enabled = _prompt_yes_no("Would you like a short tutorial? [y/N]: ", default=False)

    installed_skills = install_skills(codex_home, workspace_root, selected_agents)
    repo_dir = ensure_explore_repo(workspace_root)
    resolve_raw_data_root(workspace_root).mkdir(parents=True, exist_ok=True)
    save_recent_workspace(workspace_root, workspace_name)
    (repo_dir / workspace_name).mkdir(parents=True, exist_ok=True)

    print(f"Initialized Loom workspace at: {repo_dir.parent}")
    print(f"Initialized Loom git repo at: {repo_dir}")
    print(f"Initialized raw data root at: {resolve_raw_data_root(workspace_root)}")
    print(f"Default workspace: {workspace_name}")
    _print_installed_skills(installed_skills)

    if tutorial_enabled:
        tutorial_dir = _install_tutorial_files(workspace_root)
        print(f"Tutorial data installed at: {tutorial_dir}")
        print("Try these prompts in your agent chat:")
        print("  loom scan raw_data/cost to cost")
        print("  loom ask What is the capex for OCGT?")
        print("  loom push")
        print("Then visit https://loom-api-free.onrender.com to inspect the uploaded data.")
        input("Installation finished. Press Enter to exit.")
        return 0

    print("Agents can now use Loom with a focused skill and the default workspace you selected.")
    return 0


def _run_existing_workspace_menu(codex_home: Path, workspace_root: Path, agents: tuple[str, ...] | None) -> int:
    print("A `loom` folder already exists in this directory.")
    print("Choose an option:")
    print("  1. Learn how to reset Loom")
    print("  2. Install a skill for one agent")
    print("  3. Create a new default workspace")
    print("  4. Help")

    action = MENU_ACTIONS[_prompt_choice("Select an option [1-4]: ", tuple(MENU_ACTIONS))]
    if action == "delete":
        print("To run `loom init` from scratch again, delete the existing `./loom` folder manually first.")
        return 0
    if action == "install-skill":
        selected_agents = agents or (_prompt_agent(),)
        _print_installed_skills(install_skills(codex_home, workspace_root, selected_agents))
        print("Skill installation finished.")
        return 0
    if action == "create-workspace":
        workspace_name = _prompt_workspace_name()
        repo_dir = ensure_explore_repo(workspace_root)
        (repo_dir / workspace_name).mkdir(parents=True, exist_ok=True)
        save_recent_workspace(workspace_root, workspace_name)
        print(f"Created a new default workspace: {workspace_name}")
        print(f"Workspace path: {repo_dir / workspace_name}")
        return 0

    _print_help()
    return 0


def _prompt_agent() -> str:
    print("Which assistant do you use?")
    for index, agent in enumerate(AGENT_LABELS, start=1):
        print(f"  {index}. {AGENT_LABELS[agent]}")
    choice = _prompt_choice(f"Select an assistant [1-{len(AGENT_LABELS)}]: ", tuple(str(i) for i in range(1, len(AGENT_LABELS) + 1)))
    return tuple(AGENT_LABELS)[int(choice) - 1]


def _prompt_workspace_name() -> str:
    default_name = _default_workspace_name()
    raw_value = input(f"Default workspace name [{default_name}]: ").strip()
    return _normalize_workspace_name(raw_value or default_name)


def _prompt_yes_no(prompt: str, *, default: bool) -> bool:
    suffix = "y" if default else "n"
    while True:
        value = input(prompt).strip().lower()
        if not value:
            return default
        if value in {"y", "yes"}:
            return True
        if value in {"n", "no"}:
            return False
        print(f"Please answer yes or no. Press Enter for the default ({suffix.upper()}).")


def _prompt_choice(prompt: str, allowed: tuple[str, ...]) -> str:
    while True:
        value = input(prompt).strip()
        if value in allowed:
            return value
        print(f"Please choose one of: {', '.join(allowed)}")


def _default_workspace_name() -> str:
    try:
        user_name = getpass.getuser().strip()
    except Exception:
        user_name = ""
    return _normalize_workspace_name(user_name or "temo")


def _normalize_workspace_name(value: str) -> str:
    normalized = value.strip().replace("\\", "-").replace("/", "-")
    return normalized or "temo"


def _install_tutorial_files(workspace_root: Path) -> Path:
    target_dir = resolve_raw_data_root(workspace_root) / "cost"
    target_dir.mkdir(parents=True, exist_ok=True)
    for name, content in TUTORIAL_FILES.items():
        (target_dir / name).write_text(content, encoding="utf-8")
    return target_dir


def _print_installed_skills(installed_skills: tuple[object, ...]) -> None:
    for skill in installed_skills:
        print(f"Installed Loom skill for {skill.agent}: {skill.path}")


def _print_help() -> None:
    print("Loom quick help:")
    print("  `loom init` sets up `./loom`, `./raw_data`, your preferred agent skill, and the default workspace.")
    print("  `loom scan <path> [to <workspace>]` scans raw data into data cards.")
    print("  `loom confirm [workspace]` saves explore changes into the local git history.")
    print("  `loom push [workspace]` syncs workspaces to the default Loom API server.")
