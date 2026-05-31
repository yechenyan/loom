from __future__ import annotations

from pathlib import Path

from ..raw_cache_support import resolve_raw_data_root
from ..explore_repo import ensure_explore_repo
from ..scan_state import save_recent_workspace
from .skill import install_skills
from .tutorial_download import install_tutorial_or_warn


AGENT_LABELS = {
    "codex": "Codex(ChatGpt)",
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


def run_init_flow(
    codex_home: Path,
    workspace_root: Path,
    agents: tuple[str, ...] | None = None,
    *,
    tutorial_enabled: bool = True,
    tutorial_url: str | None = None,
    tutorial_sha256: str | None = None,
    force_tutorial: bool = False,
) -> int:
    if agents:
        return _run_fast_init(
            codex_home,
            workspace_root,
            agents,
            tutorial_enabled,
            tutorial_url,
            tutorial_sha256,
            force_tutorial,
        )
    loom_root = workspace_root / "loom"
    if loom_root.exists():
        return _run_existing_workspace_menu(codex_home, workspace_root, agents)
    return _run_fresh_init(
        codex_home,
        workspace_root,
        agents,
        tutorial_enabled,
        tutorial_url,
        tutorial_sha256,
        force_tutorial,
    )


def _run_fresh_init(
    codex_home: Path,
    workspace_root: Path,
    agents: tuple[str, ...] | None,
    tutorial_enabled: bool,
    tutorial_url: str | None,
    tutorial_sha256: str | None,
    force_tutorial: bool,
) -> int:
    selected_agents = agents or (_prompt_agent(),)
    workspace_name = _prompt_workspace_name()
    tutorial_enabled = tutorial_enabled and _prompt_install_tutorial()
    repo_dir, installed_skills = _initialize_workspace(codex_home, workspace_root, selected_agents, workspace_name)
    _print_init_summary(workspace_root, repo_dir, workspace_name, installed_skills, reused=False)
    if tutorial_enabled:
        install_tutorial_or_warn(workspace_root, url=tutorial_url, sha256=tutorial_sha256, force=force_tutorial)
        _print_chat_and_terminal_guide()
        return 0
    print("Agents can now use Loom with focused skills and the default workspace you selected.")
    print("Remember: `loom` is chat and `loomcli` is the execution command for both users and agents.")
    return 0


def _run_fast_init(
    codex_home: Path,
    workspace_root: Path,
    agents: tuple[str, ...],
    tutorial_enabled: bool,
    tutorial_url: str | None,
    tutorial_sha256: str | None,
    force_tutorial: bool,
) -> int:
    workspace_name = _default_workspace_name()
    reused = (workspace_root / "loom").exists()
    repo_dir, installed_skills = _initialize_workspace(codex_home, workspace_root, agents, workspace_name)
    _print_init_summary(workspace_root, repo_dir, workspace_name, installed_skills, reused=reused)
    if tutorial_enabled:
        install_tutorial_or_warn(workspace_root, url=tutorial_url, sha256=tutorial_sha256, force=force_tutorial)
    else:
        print("Tutorial data download skipped because `--no-tutorial` was provided.")
    print("Fast init mode is active because `--agent` was provided, so Loom skipped the interactive setup.")
    _print_chat_and_terminal_guide()
    return 0


def _run_existing_workspace_menu(codex_home: Path, workspace_root: Path, agents: tuple[str, ...] | None) -> int:
    print("A `loom` folder already exists in this directory.")
    print("Choose an option:")
    print("  1. Learn how to reset Loom")
    print("  2. Install Loom skills for one agent")
    print("  3. Create a new default workspace")
    print("  4. Help")

    action = MENU_ACTIONS[_prompt_choice("Select an option [1-4]: ", tuple(MENU_ACTIONS))]
    if action == "delete":
        print("To run `loomcli init` from scratch again, delete the existing `./loom` folder manually first.")
        return 0
    if action == "install-skill":
        selected_agents = agents or (_prompt_agent(),)
        _print_installed_skills(install_skills(codex_home, workspace_root, selected_agents))
        print("Loom skills installed.")
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


def _initialize_workspace(
    codex_home: Path,
    workspace_root: Path,
    selected_agents: tuple[str, ...],
    workspace_name: str,
) -> tuple[Path, tuple[object, ...]]:
    installed_skills = install_skills(codex_home, workspace_root, selected_agents)
    repo_dir = ensure_explore_repo(workspace_root)
    resolve_raw_data_root(workspace_root).mkdir(parents=True, exist_ok=True)
    save_recent_workspace(workspace_root, workspace_name)
    (repo_dir / workspace_name).mkdir(parents=True, exist_ok=True)
    return repo_dir, installed_skills


def _print_init_summary(
    workspace_root: Path,
    repo_dir: Path,
    workspace_name: str,
    installed_skills: tuple[object, ...],
    *,
    reused: bool,
) -> None:
    status = "Reused existing Loom workspace at" if reused else "Initialized Loom workspace at"
    print(f"{status}: {workspace_root / 'loom'}")
    print(f"Initialized Loom git repo at: {repo_dir}")
    print(f"Initialized raw data root at: {resolve_raw_data_root(workspace_root)}")
    print(f"Default workspace: {workspace_name}")
    _print_installed_skills(installed_skills)


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


def _prompt_install_tutorial() -> bool:
    value = input("Would you like a short tutorial? [Y/n]: ").strip().lower()
    return value not in {"n", "no"}


def _prompt_choice(prompt: str, allowed: tuple[str, ...]) -> str:
    while True:
        value = input(prompt).strip()
        if value in allowed:
            return value
        print(f"Please choose one of: {', '.join(allowed)}")


def _default_workspace_name() -> str:
    return "demo"


def _normalize_workspace_name(value: str) -> str:
    normalized = value.strip().replace("\\", "-").replace("/", "-")
    return normalized or "demo"


def _print_installed_skills(installed_skills: tuple[object, ...]) -> None:
    for skill in installed_skills:
        print(f"Installed Loom skill for {skill.agent}: {skill.path}")


def _print_help() -> None:
    print("Loom quick help:")
    print("  `loom` is the chat prompt form, for example `loom scan raw_data/energy`.")
    print("  `loomcli init --agent codex` is the non-interactive fast path and downloads the tutorial automatically.")
    print("  `loomcli init` sets up `./loom`, `./raw_data`, your preferred agent skills, and the default workspace.")
    print("  `loomcli scan-index <path> [to <workspace>]` builds Loom cards from the terminal when you want an explicit CLI scan.")
    print("  `loomcli confirm [workspace]` saves explore changes into the local git history.")
    print("  `loomcli push [workspace]` syncs workspaces to the default Loom API server.")


def _print_chat_and_terminal_guide() -> None:
    print("Loom now uses two names: `loom` for chat and `loomcli` for execution.")
    print("Do not run the `loom ...` lines in your shell.")
    print("Tell the user to keep these in AI chat:")
    print("  loom scan raw_data/demo_germany_energy_data to germany_energy")
    print('  loom ask "What German wind and solar data is available?"')
    print("  loom 德国 2015 年有哪些发电装机容量数据？")
    print("Tell the user to keep these in the terminal:")
    print("  loomcli scan-index raw_data/demo_germany_energy_data to germany_energy")
    print("  loomcli confirm germany_energy")
    print("  loomcli push germany_energy")
    print("  loomcli get germany_energy/demo_germany_energy_data/open_power_system_data/time_series/germany_2015_new_year_day_power.csv")
