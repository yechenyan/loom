from __future__ import annotations

import importlib
import sys

from .handlers import run_ask, run_confirm, run_get, run_init, run_pull, run_pull_raw, run_push, run_scan, run_set_api, run_status
from .parser import build_parser
from .routing import run_route


KNOWN_COMMANDS = {
    "ask",
    "confirm",
    "get",
    "init",
    "install",
    "pull",
    "pull-raw",
    "push",
    "route",
    "scan",
    "server-init-db",
    "server-run",
    "set-api",
    "status",
}


def main(argv: list[str] | None = None) -> int:
    normalized_argv = _normalize_argv(sys.argv[1:] if argv is None else argv)
    args = build_parser().parse_args(normalized_argv)
    handlers = {
        "init": run_init,
        "install": run_init,
        "scan": run_scan,
        "route": run_route,
        "ask": run_ask,
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


def _normalize_argv(argv: list[str]) -> list[str]:
    if not argv:
        return argv
    first = argv[0].strip().lower()
    if first and not first.startswith("-") and first not in KNOWN_COMMANDS:
        return ["ask", *argv]
    return argv
