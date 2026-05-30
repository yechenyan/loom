from __future__ import annotations

import argparse
import os
from pathlib import Path

from .config import (
    DEFAULT_DATABASE_URL,
    DEFAULT_SERVER_HOST,
    DEFAULT_SERVER_PORT,
    DEFAULT_SERVER_URL,
    DEFAULT_SERVER_WORKSPACE_ROOT,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="loomcli")
    subparsers = parser.add_subparsers(dest="command")
    _add_init_parser(subparsers)
    _add_public_scan_parser(subparsers)
    _add_data_parsers(subparsers)
    _add_sync_parsers(subparsers)
    return parser


def _add_init_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    init_parser = subparsers.add_parser(
        "init",
        help="Interactively initialize Loom, install agent skills, and prepare the local Loom git workspace.",
    )
    init_parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    init_parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    init_parser.add_argument(
        "--agent",
        dest="agents",
        action="append",
        choices=("codex", "claude", "cursor", "copilot"),
        help="Run `loomcli init` in a non-interactive fast path for the selected assistant and install the tutorial dataset.",
    )


def _add_public_scan_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    scan_parser = subparsers.add_parser(
        "scan-index",
        help="Scan a source directory and build Loom cards/index files under a workspace.",
    )
    scan_parser.add_argument("scan_args", nargs="*")
    scan_parser.add_argument("--workspace-root", type=Path, default=Path.cwd())


def _add_data_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    set_api_parser = subparsers.add_parser("set-api", help="Persist the default Loom sync server base URL for future CLI commands.")
    set_api_parser.add_argument("base_url")

    get_parser = subparsers.add_parser("get", help="Ensure one raw file exists under loom/.loom/raw and print its local path.")
    get_parser.add_argument("resource")
    get_parser.add_argument("--server-url", default=DEFAULT_SERVER_URL)
    get_parser.add_argument("--workspace-root", type=Path, default=Path.cwd())

    pull_raw_parser = subparsers.add_parser("pull-raw", help="Pull latest raw files into loom/.loom/raw.")
    pull_raw_parser.add_argument("workspace", nargs="?")
    pull_raw_parser.add_argument("--server-url", default=DEFAULT_SERVER_URL)
    pull_raw_parser.add_argument("--workspace-root", type=Path, default=Path.cwd())


def _add_sync_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    _add_workspace_parser(subparsers, "status", "Show pending Loom workspace changes.", include_message=False)
    _add_workspace_parser(subparsers, "confirm", "Commit pending Loom workspace changes.", include_message=True)
    _add_workspace_parser(subparsers, "push", "Push local workspaces to the Loom sync server.", include_message=True, include_server=True)
    _add_workspace_parser(subparsers, "pull", "Pull remote workspaces from the Loom sync server.", include_server=True)

    init_parser = subparsers.add_parser("server-init-db", help="Initialize the Loom sync server database schema.")
    init_parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    init_parser.add_argument("--storage-root", type=Path, default=Path(os.environ.get("LOOM_SERVER_STORAGE_ROOT", Path.cwd() / ".loom-server-storage")))
    init_parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path(DEFAULT_SERVER_WORKSPACE_ROOT) if DEFAULT_SERVER_WORKSPACE_ROOT else Path.cwd(),
    )

    run_parser = subparsers.add_parser("server-run", help="Run the Loom sync FastAPI server.")
    run_parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    run_parser.add_argument("--storage-root", type=Path, default=Path(os.environ.get("LOOM_SERVER_STORAGE_ROOT", Path.cwd() / ".loom-server-storage")))
    run_parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path(DEFAULT_SERVER_WORKSPACE_ROOT) if DEFAULT_SERVER_WORKSPACE_ROOT else Path.cwd(),
    )
    run_parser.add_argument("--host", default=DEFAULT_SERVER_HOST)
    run_parser.add_argument("--port", type=int, default=DEFAULT_SERVER_PORT)


def _add_workspace_parser(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    name: str,
    help_text: str,
    *,
    include_message: bool = False,
    include_server: bool = False,
) -> None:
    parser = subparsers.add_parser(name, help=help_text)
    parser.add_argument("workspace", nargs="?")
    if include_message:
        parser.add_argument("--message")
    if include_server:
        parser.add_argument("--server-url", default=DEFAULT_SERVER_URL)
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
