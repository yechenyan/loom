from __future__ import annotations

import importlib
import sys

from .handlers import run_confirm, run_get, run_install, run_pull, run_pull_raw, run_push, run_scan, run_set_api, run_status
from .parser import build_parser
from .routing import run_route


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "install": run_install,
        "scan": run_scan,
        "route": run_route,
        "set-api": run_set_api,
        "get": run_get,
        "status": run_status,
        "confirm": run_confirm,
        "push": run_push,
        "pull": run_pull,
        "pull-raw": run_pull_raw,
    }
    if args.command in handlers:
        return handlers[args.command](args)
    if args.command == "server-init-db":
        return _run_server_command("run_init_db", args.database_url, args.storage_root, args.workspace_root)
    if args.command == "server-run":
        return _run_server_command("run_server", args.database_url, args.storage_root, args.workspace_root, args.host, args.port)
    build_parser().print_help()
    return 1


def _run_server_command(function_name: str, *args: object) -> int:
    try:
        module = importlib.import_module("loom_server.cli")
    except ModuleNotFoundError as exc:
        if exc.name == "loom_server":
            print(
                "This command requires the separate 'loom-server' package. "
                "Install it first, then rerun the command.",
                file=sys.stderr,
            )
            return 1
        raise

    command = getattr(module, function_name)
    return int(command(*args))
