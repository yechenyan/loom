from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

import psycopg2
import sqlalchemy as sa

from .chat import parse_chat_request, parse_loom_command
from .data import get as get_resource
from .explore_repo import confirm_changes, ensure_explore_repo, get_repo_status
from .scanner import scan_topic_from_chat, scan_topic_to_explore
from .sync_client import pull_raw_workspaces, pull_workspaces, push_workspaces
from .sync_server import create_app
from .sync_state import load_workspace_sync_state


DEFAULT_DATABASE_URL = os.environ.get(
    "LOOM_SERVER_DATABASE_URL",
    "postgresql+psycopg2://loom@127.0.0.1:5432/loom",
)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "install":
        return _run_install(args)
    if args.command == "scan":
        return _run_scan(args)
    if args.command == "route":
        return _run_route(args)
    if args.command == "get":
        return _run_get(args)
    if args.command == "status":
        return _run_status(args)
    if args.command == "confirm":
        return _run_confirm(args)
    if args.command == "push":
        return _run_push(args)
    if args.command == "pull":
        return _run_pull(args)
    if args.command == "pull-raw":
        return _run_pull_raw(args)
    if args.command == "server-init-db":
        return _run_server_init_db(args)
    if args.command == "server-run":
        return _run_server_run(args)

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

    get_parser = subparsers.add_parser(
        "get",
        help="Ensure one raw file exists under test-project/loom/.loom/raw and print its local path.",
    )
    get_parser.add_argument("resource", help="Raw resource path in the form workspace/path/to/file")
    get_parser.add_argument(
        "--server-url",
        default=os.environ.get("LOOM_SERVER_URL", "http://127.0.0.1:8765"),
        help="Base URL for the Loom sync server.",
    )
    get_parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root that contains test-project/loom/.loom/raw.",
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
    status_parser.add_argument(
        "--server-url",
        default=os.environ.get("LOOM_SERVER_URL", "http://127.0.0.1:8765"),
        help="Base URL for the Loom sync server. Only used when printing sync hints.",
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

    push_parser = subparsers.add_parser(
        "push",
        help="Push one workspace or all local workspaces to the Loom sync server.",
    )
    push_parser.add_argument("workspace", nargs="?", help="Workspace to push, such as energy.")
    push_parser.add_argument(
        "--message",
        help="Optional push message recorded in the server revision metadata.",
    )
    push_parser.add_argument(
        "--server-url",
        default=os.environ.get("LOOM_SERVER_URL", "http://127.0.0.1:8765"),
        help="Base URL for the Loom sync server.",
    )
    push_parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root that contains this repo.",
    )

    pull_parser = subparsers.add_parser(
        "pull",
        help="Pull one workspace or all remote workspaces from the Loom sync server.",
    )
    pull_parser.add_argument("workspace", nargs="?", help="Workspace to pull, such as energy.")
    pull_parser.add_argument(
        "--server-url",
        default=os.environ.get("LOOM_SERVER_URL", "http://127.0.0.1:8765"),
        help="Base URL for the Loom sync server.",
    )
    pull_parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root that contains this repo.",
    )

    pull_raw_parser = subparsers.add_parser(
        "pull-raw",
        help="Pull the latest raw files into test-project/loom/.loom/raw for one workspace or all workspaces.",
    )
    pull_raw_parser.add_argument("workspace", nargs="?", help="Workspace to pull raw files for, such as energy.")
    pull_raw_parser.add_argument(
        "--server-url",
        default=os.environ.get("LOOM_SERVER_URL", "http://127.0.0.1:8765"),
        help="Base URL for the Loom sync server.",
    )
    pull_raw_parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path.cwd(),
        help="Workspace root that contains test-project/loom/.loom/raw.",
    )

    server_init_db_parser = subparsers.add_parser(
        "server-init-db",
        help="Initialize the Loom sync server database schema.",
    )
    server_init_db_parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help="SQLAlchemy database URL for the Loom sync server.",
    )
    server_init_db_parser.add_argument(
        "--storage-root",
        type=Path,
        default=Path(os.environ.get("LOOM_SERVER_STORAGE_ROOT", Path.cwd() / ".loom-server-storage")),
        help="Filesystem root where server snapshots are stored.",
    )

    server_run_parser = subparsers.add_parser(
        "server-run",
        help="Run the Loom sync FastAPI server.",
    )
    server_run_parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help="SQLAlchemy database URL for the Loom sync server.",
    )
    server_run_parser.add_argument(
        "--storage-root",
        type=Path,
        default=Path(os.environ.get("LOOM_SERVER_STORAGE_ROOT", Path.cwd() / ".loom-server-storage")),
        help="Filesystem root where server snapshots are stored.",
    )
    server_run_parser.add_argument("--host", default="127.0.0.1", help="Host to bind the FastAPI server to.")
    server_run_parser.add_argument("--port", type=int, default=8765, help="Port to bind the FastAPI server to.")

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
    print(f"Datasets discovered: {result.dataset_count}")
    print(f"Datasets rebuilt: {len(result.rebuilt_dataset_dirs)}")
    for dataset_dir in result.rebuilt_dataset_dirs:
        print(f"- rebuilt: {dataset_dir}")
    print(f"Datasets skipped: {len(result.skipped_dataset_dirs)}")
    for dataset_dir in result.skipped_dataset_dirs:
        print(f"- skipped: {dataset_dir}")
    if result.missing_dataset_dirs:
        print(f"Missing source datasets kept in explore: {len(result.missing_dataset_dirs)}")
        for relative_dir in result.missing_dataset_dirs:
            print(f"- kept: {relative_dir}")
    _print_status_summary(args.workspace_root, args.topic)
    return 0


def _run_route(args: argparse.Namespace) -> int:
    request = parse_loom_command(args.message)
    if request is None:
        print("No loom command detected.")
        return 1

    if request.command == "scan":
        result = scan_topic_from_chat(args.message, args.workspace_root)
        if result is None:
            print("No loom scan command detected.")
            return 1
        print(f"Detected loom scan chat command for topic: {request.workspace}")
        print(f"Explore directory: {result.explore_topic_dir}")
        _print_status_summary(args.workspace_root, request.workspace or "")
        return 0

    if request.command == "status":
        route_args = argparse.Namespace(
            workspace=request.workspace,
            workspace_root=args.workspace_root,
            server_url=os.environ.get("LOOM_SERVER_URL", "http://127.0.0.1:8765"),
        )
        print(f"Detected loom status chat command for workspace: {request.workspace or 'all'}")
        return _run_status(route_args)

    if request.command == "confirm":
        route_args = argparse.Namespace(
            workspace=request.workspace,
            workspace_root=args.workspace_root,
            message=None,
        )
        print(f"Detected loom confirm chat command for workspace: {request.workspace or 'all'}")
        return _run_confirm(route_args)

    if request.command == "push":
        route_args = argparse.Namespace(
            workspace=request.workspace,
            workspace_root=args.workspace_root,
            message=None,
            server_url=os.environ.get("LOOM_SERVER_URL", "http://127.0.0.1:8765"),
        )
        print(f"Detected loom push chat command for workspace: {request.workspace or 'all'}")
        return _run_push(route_args)

    if request.command == "pull":
        route_args = argparse.Namespace(
            workspace=request.workspace,
            workspace_root=args.workspace_root,
            server_url=os.environ.get("LOOM_SERVER_URL", "http://127.0.0.1:8765"),
        )
        print(f"Detected loom pull chat command for workspace: {request.workspace or 'all'}")
        return _run_pull(route_args)

    print("No loom command detected.")
    return 1


def _run_get(args: argparse.Namespace) -> int:
    local_path = get_resource(args.resource, workspace_root=args.workspace_root, server_url=args.server_url)
    print(f"Cached resource: {args.resource}")
    print(f"Local path: {local_path}")
    return 0


def _run_status(args: argparse.Namespace) -> int:
    status = get_repo_status(args.workspace_root, args.workspace)
    print(f"Explore repo: {status.repo_dir}")
    if status.scope:
        print(f"Workspace: {status.scope}")
        state = load_workspace_sync_state(args.workspace_root, status.scope)
        print(f"Last pulled revision: {state.last_pulled_revision or '-'}")
        print(f"Last pushed revision: {state.last_pushed_revision or '-'}")
        print(f"Last synced tree hash: {state.last_synced_tree_hash or '-'}")
        print(f"Last sync commit: {state.last_sync_commit or '-'}")
        if state.pending_rebase_revision:
            print(f"Pending rebase revision: {state.pending_rebase_revision}")

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


def _run_push(args: argparse.Namespace) -> int:
    results = push_workspaces(args.workspace_root, args.server_url, args.workspace, args.message)
    if not results:
        print("No local workspaces found to push.")
        return 0

    exit_code = 0
    for result in results:
        if result.conflicted:
            exit_code = 1
            print(f"Push paused for workspace: {result.workspace}")
            print(f"Remote revision: {result.revision_id or '-'}")
            print("Conflict detected during rebase. Resolve the files below, then run:")
            print(f"  loom confirm {result.workspace}")
            print(f"  loom push {result.workspace}")
            for path in result.conflict_paths:
                print(f"- conflict: {path}")
            continue
        print(f"Pushed workspace: {result.workspace}")
        print(f"Revision: {result.revision_id}")
        print(f"Tree hash: {result.tree_hash}")
        print(f"Changed files: {result.changed_file_count}")
        print(f"Deleted files: {result.deleted_file_count}")
        print(f"Raw objects uploaded: {result.raw_uploaded_object_count}")
        print(f"Raw path mappings changed: {result.raw_mapping_changed_count}")
        print(f"Raw path mappings deleted: {result.raw_mapping_deleted_count}")
        if result.raw_conflict_notice_path:
            print(f"Raw conflict notice: {result.raw_conflict_notice_path}")
    return exit_code


def _run_pull(args: argparse.Namespace) -> int:
    results = pull_workspaces(args.workspace_root, args.server_url, args.workspace)
    if not results:
        print("No remote workspaces found to pull.")
        return 0

    exit_code = 0
    for result in results:
        print(f"Pulled workspace: {result.workspace}")
        print(f"Revision: {result.revision_id}")
        print(f"Changed: {'yes' if result.changed else 'no'}")
        print(f"Changed files: {result.changed_file_count}")
        print(f"Deleted files: {result.deleted_file_count}")
        if result.conflicted:
            exit_code = 1
            print("Conflict detected during rebase. Resolve the files below, then run:")
            print(f"  loom confirm {result.workspace}")
            print(f"  loom push {result.workspace}")
            for path in result.conflict_paths:
                print(f"- conflict: {path}")
        elif result.raw_conflict_notice_path:
            print(f"Raw conflict notice: {result.raw_conflict_notice_path}")
    return exit_code


def _run_pull_raw(args: argparse.Namespace) -> int:
    results = pull_raw_workspaces(args.workspace_root, args.server_url, args.workspace)
    if not results:
        print("No remote workspaces found to pull raw files for.")
        return 0

    for result in results:
        print(f"Pulled raw workspace: {result.workspace}")
        print(f"Manifest files: {result.manifest_file_count}")
        print(f"Downloaded files: {result.downloaded_file_count}")
        print(f"Linked local files: {result.linked_file_count}")
        print(f"Deleted files: {result.deleted_file_count}")
        if result.raw_conflict_notice_path:
            print(f"Raw conflict notice: {result.raw_conflict_notice_path}")
    return 0


def _run_server_init_db(args: argparse.Namespace) -> int:
    _ensure_database_exists(args.database_url)
    app = create_app(args.database_url, args.storage_root)
    app.state.sync_service.init_db()
    print(f"Initialized Loom sync database: {args.database_url}")
    print(f"Storage root: {args.storage_root}")
    return 0


def _run_server_run(args: argparse.Namespace) -> int:
    import uvicorn

    _ensure_database_exists(args.database_url)
    app = create_app(args.database_url, args.storage_root)
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


def _ensure_database_exists(database_url: str) -> None:
    url = sa.engine.make_url(database_url)
    if not str(url.drivername).startswith("postgresql"):
        return

    database_name = url.database
    if not database_name:
        return

    maintenance_database = "postgres"
    connect_kwargs = {
        "dbname": maintenance_database,
        "user": url.username,
        "password": url.password,
        "host": url.host,
        "port": url.port,
    }
    connect_kwargs = {key: value for key, value in connect_kwargs.items() if value is not None}

    with psycopg2.connect(**connect_kwargs) as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
            exists = cursor.fetchone() is not None
            if not exists:
                cursor.execute(f'CREATE DATABASE "{database_name}"')


def _render_skill_markdown(workspace_root: Path, launcher: Path) -> str:
    return f"""# loom-scan

Use this skill when the user types a Loom request in chat, especially commands like `loom scan energy` or `loom confirm energy`.

## Purpose

- Provide a fast path for Loom scan requests without doing broad repo exploration first.
- Generate dataset summaries under `test-project/loom/loom_explore/<topic>`.
- Track confirmed loom_explore changes in a dedicated git repository.
- Route sync commands like `loom push energy` and `loom pull energy` into the local CLI fast path.
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

## Other Commands

- `loom status <workspace>`
- `loom confirm <workspace>`
- `loom push <workspace>`
- `loom pull <workspace>`
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
