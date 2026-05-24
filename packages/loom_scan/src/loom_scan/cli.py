from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

from .chat import parse_chat_request
from .explore_repo import confirm_changes, ensure_explore_repo, get_repo_status
from .scanner import scan_topic_from_chat, scan_topic_to_explore


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "install":
        return _run_install(args)
    if args.command == "scan":
        return _run_scan(args)
    if args.command == "route":
        return _run_route(args)
    if args.command == "status":
        return _run_status(args)
    if args.command == "confirm":
        return _run_confirm(args)

    parser.print_help()
    return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="loom")
    subparsers = parser.add_subparsers(dest="command")

    install_parser = subparsers.add_parser(
        "install",
        help="Install the Loom Codex skill and initialize loom_explore git tracking.",
    )
    install_parser.add_argument(
        "--codex-home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")),
        help="Target Codex home directory. Defaults to $CODEX_HOME or ~/.codex.",
    )
    install_parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root that contains this repo.",
    )

    scan_parser = subparsers.add_parser(
        "scan",
        help="Scan a Loom topic from loom_raw into loom_explore.",
    )
    scan_parser.add_argument("topic", help="Topic under test-project/loom/loom_raw")
    scan_parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root that contains this repo.",
    )

    route_parser = subparsers.add_parser(
        "route",
        help="Parse a chat message and run loom scan if it matches.",
    )
    route_parser.add_argument("message", help="Chat message to inspect.")
    route_parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root that contains this repo.",
    )

    status_parser = subparsers.add_parser(
        "status",
        help="Show pending loom_explore changes, optionally filtered to one workspace.",
    )
    status_parser.add_argument(
        "workspace",
        nargs="?",
        help="Top-level workspace under test-project/loom/loom_explore, such as energy.",
    )
    status_parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root that contains this repo.",
    )

    confirm_parser = subparsers.add_parser(
        "confirm",
        help="Commit pending loom_explore changes, optionally for one workspace.",
    )
    confirm_parser.add_argument(
        "workspace",
        nargs="?",
        help="Top-level workspace under test-project/loom/loom_explore, such as energy.",
    )
    confirm_parser.add_argument(
        "--message",
        help="Optional commit message for the confirmation commit.",
    )
    confirm_parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root that contains this repo.",
    )

    return parser


def _run_install(args: argparse.Namespace) -> int:
    codex_home = args.codex_home.resolve()
    workspace_root = args.workspace_root.resolve()
    skill_dir = codex_home / "skills" / "loom-scan"
    skill_dir.mkdir(parents=True, exist_ok=True)

    launcher = workspace_root / "scripts" / "loom.py"
    skill_content = _render_skill_markdown(workspace_root, launcher)
    (skill_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")

    repo_dir = ensure_explore_repo(workspace_root)

    print(f"Installed Loom scan skill to: {skill_dir}")
    print(f"Initialized loom_explore git repo at: {repo_dir}")
    print("Codex can now use a fast path for chat messages like `loom scan energy`.")
    print("Recommended scan command:")
    print(f"  uv run python {launcher} scan energy")
    print("Recommended confirm command:")
    print(f"  uv run python {launcher} confirm energy")
    return 0


def _run_scan(args: argparse.Namespace) -> int:
    result = scan_topic_to_explore(args.topic, args.workspace_root)
    print(f"Scanned topic: {result.topic}")
    print(f"Raw directory: {result.raw_topic_dir}")
    print(f"Explore directory: {result.explore_topic_dir}")
    print(f"Datasets written: {result.dataset_count}")
    for dataset_dir in result.dataset_dirs:
        print(f"- {dataset_dir}")
    _print_status_summary(args.workspace_root, args.topic)
    return 0


def _run_route(args: argparse.Namespace) -> int:
    request = parse_chat_request(args.message)
    if request is None:
        print("No loom scan command detected.")
        return 1

    result = scan_topic_from_chat(args.message, args.workspace_root)
    if result is None:
        print("No loom scan command detected.")
        return 1

    print(f"Detected loom scan chat command for topic: {request.topic}")
    print(f"Explore directory: {result.explore_topic_dir}")
    _print_status_summary(args.workspace_root, request.topic)
    return 0


def _run_status(args: argparse.Namespace) -> int:
    status = get_repo_status(args.workspace_root, args.workspace)
    print(f"Explore repo: {status.repo_dir}")
    if status.scope:
        print(f"Workspace: {status.scope}")

    if not status.entries:
        print("No pending changes.")
        return 0

    print("Pending changes:")
    for entry in status.entries:
        print(f"{entry.code} {entry.path}")
    return 0


def _run_confirm(args: argparse.Namespace) -> int:
    commit_hash = confirm_changes(args.workspace_root, args.workspace, args.message)
    if commit_hash is None:
        print("No pending changes to confirm.")
        return 0

    scope_text = args.workspace or "all workspaces"
    print(f"Confirmed changes for {scope_text}.")
    print(f"Commit: {commit_hash}")
    return 0


def _render_skill_markdown(workspace_root: Path, launcher: Path) -> str:
    return f"""# loom-scan

Use this skill when the user types a Loom request in chat, especially commands like `loom scan energy` or `loom confirm energy`.

## Purpose

- Provide a fast path for Loom scan requests without doing broad repo exploration first.
- Generate dataset summaries under `test-project/loom/loom_explore/<topic>`.
- Track confirmed loom_explore changes in a dedicated git repository.
- Prefer reading `loom_explore` outputs after the scan instead of reading raw CSV files directly.

## Fast Path

When the user message matches `loom scan <topic>`:

1. Do not browse unrelated files first.
2. Do not read anything under `wiki/discard`.
3. Run this command from the repo root:

```bash
uv run python {launcher} route "loom scan <topic>" --workspace-root {workspace_root}
```

4. If you already know the topic, you can run the direct scan command instead:

```bash
uv run python {launcher} scan <topic> --workspace-root {workspace_root}
```

## After Scanning

- Read the generated files under `test-project/loom/loom_explore/<topic>`.
- Show the user pending changes and suggest `loom confirm <topic>` once the generated files look right.
- Prefer machine-readable summaries like `profile.json`.
- Only fall back to `loom_raw` if the generated explore files are missing or obviously incomplete.
"""


def _print_status_summary(workspace_root: Path | str, workspace: str) -> None:
    status = get_repo_status(workspace_root, workspace)
    if not status.entries:
        print("No pending changes detected after scan.")
        return

    launcher = Path(workspace_root).resolve() / "scripts" / "loom.py"
    print("Pending changes:")
    for entry in status.entries:
        print(f"{entry.code} {entry.path}")
    print(f"Confirm with: uv run python {launcher} confirm {workspace}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
