from __future__ import annotations

import sys

from .handlers import run_scan
from .parser import build_run_parser
from .routing import run_route


def main(argv: list[str] | None = None) -> int:
    args = build_run_parser().parse_args(sys.argv[1:] if argv is None else argv)
    handlers = {
        "route": run_route,
        "scan": run_scan,
    }
    if args.command in handlers:
        return handlers[args.command](args)
    build_run_parser().print_help()
    return 1
