from __future__ import annotations

import argparse

from ..chat import parse_loom_command
from ..scanner import DuplicateDatasetPathError, scan_topic_from_chat
from .ask_flow import run_ask_query
from .config import DEFAULT_SERVER_URL
from .handlers import run_confirm, run_pull, run_push, run_status
from .output import print_status_summary


def run_route(args: argparse.Namespace) -> int:
    request = parse_loom_command(args.message)
    if request is None:
        print("No loom command detected.")
        return 1
    if request.command == "scan":
        if request.source_path is None:
            print("Missing scan path. Use `loom scan <path> [to <workspace>]`.")
            return 1
        try:
            result = scan_topic_from_chat(args.message, args.workspace_root)
        except DuplicateDatasetPathError as exc:
            print(str(exc))
            return 1
        if result is None:
            print("No loom scan command detected.")
            return 1
        print(f"Detected loom scan chat command for workspace: {result.topic}")
        print_status_summary(args.workspace_root, result.topic)
        return 0
    if request.command == "ask":
        if not request.query:
            print("Missing ask query. Use `loom ask <question>` or `loom <question>`.")
            return 1
        return run_ask_query(request.query, args.workspace_root, DEFAULT_SERVER_URL)
    route_args = argparse.Namespace(
        workspace=request.workspace,
        workspace_root=args.workspace_root,
        server_url=DEFAULT_SERVER_URL,
        message=None,
    )
    handlers = {"status": run_status, "confirm": run_confirm, "push": run_push, "pull": run_pull}
    return handlers.get(request.command, _no_command)(route_args)


def _no_command(_: argparse.Namespace) -> int:
    print("No loom command detected.")
    return 1
