from __future__ import annotations

import argparse

from ..chat import parse_loom_command
from ..scanner import scan_topic_from_chat
from .config import DEFAULT_SERVER_URL
from .handlers import run_confirm, run_pull, run_push, run_status
from .output import print_status_summary


def run_route(args: argparse.Namespace) -> int:
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
        print_status_summary(args.workspace_root, request.workspace or "")
        return 0
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
