from __future__ import annotations

import argparse
import os
from pathlib import Path

from .config import DEFAULT_DATABASE_URL, DEFAULT_SERVER_URL


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="loom")
    subparsers = parser.add_subparsers(dest="command")
    _add_install_parser(subparsers)
    _add_scan_parsers(subparsers)
    _add_data_parsers(subparsers)
    _add_sync_parsers(subparsers)
    return parser


def _add_install_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    install_parser = subparsers.add_parser("install", help="Install the Loom Codex skill and initialize loom_explore git tracking.")
    install_parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")))
    install_parser.add_argument("--workspace-root", type=Path, default=Path.cwd())


def _add_scan_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    scan_parser = subparsers.add_parser("scan", help="Scan a Loom topic from loom_raw into loom_explore.")
    scan_parser.add_argument("topic")
    scan_parser.add_argument("--workspace-root", type=Path, default=Path.cwd())

    route_parser = subparsers.add_parser("route", help="Parse a chat message and run loom scan if it matches.")
    route_parser.add_argument("message")
    route_parser.add_argument("--workspace-root", type=Path, default=Path.cwd())


def _add_data_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    get_parser = subparsers.add_parser("get", help="Ensure one raw file exists under test-project/loom/.loom/raw and print its local path.")
    get_parser.add_argument("resource")
    get_parser.add_argument("--server-url", default=DEFAULT_SERVER_URL)
    get_parser.add_argument("--workspace-root", type=Path, default=Path.cwd())

    pull_raw_parser = subparsers.add_parser("pull-raw", help="Pull latest raw files into test-project/loom/.loom/raw.")
    pull_raw_parser.add_argument("workspace", nargs="?")
    pull_raw_parser.add_argument("--server-url", default=DEFAULT_SERVER_URL)
    pull_raw_parser.add_argument("--workspace-root", type=Path, default=Path.cwd())


def _add_sync_parsers(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    _add_workspace_parser(subparsers, "status", "Show pending loom_explore changes.", include_message=False)
    _add_workspace_parser(subparsers, "confirm", "Commit pending loom_explore changes.", include_message=True)
    _add_workspace_parser(subparsers, "push", "Push local workspaces to the Loom sync server.", include_message=True, include_server=True)
    _add_workspace_parser(subparsers, "pull", "Pull remote workspaces from the Loom sync server.", include_server=True)

    init_parser = subparsers.add_parser("server-init-db", help="Initialize the Loom sync server database schema.")
    init_parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    init_parser.add_argument("--storage-root", type=Path, default=Path(os.environ.get("LOOM_SERVER_STORAGE_ROOT", Path.cwd() / ".loom-server-storage")))

    run_parser = subparsers.add_parser("server-run", help="Run the Loom sync FastAPI server.")
    run_parser.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    run_parser.add_argument("--storage-root", type=Path, default=Path(os.environ.get("LOOM_SERVER_STORAGE_ROOT", Path.cwd() / ".loom-server-storage")))
    run_parser.add_argument("--host", default="127.0.0.1")
    run_parser.add_argument("--port", type=int, default=8765)


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
