from __future__ import annotations

from .handlers import run_confirm, run_get, run_install, run_pull, run_pull_raw, run_push, run_scan, run_status
from .parser import build_parser
from .routing import run_route


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handlers = {
        "install": run_install,
        "scan": run_scan,
        "route": run_route,
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
        from loom_server.cli import run_init_db

        return run_init_db(args.database_url, args.storage_root)
    if args.command == "server-run":
        from loom_server.cli import run_server

        return run_server(args.database_url, args.storage_root, args.host, args.port)
    build_parser().print_help()
    return 1
