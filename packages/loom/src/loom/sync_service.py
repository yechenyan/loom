from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["__getattr__", "__dir__"]


def __getattr__(name: str) -> Any:
    try:
        module = import_module("loom_server.sync_service")
    except ModuleNotFoundError as exc:
        if exc.name == "loom_server":
            raise ModuleNotFoundError(
                "loom.sync_service requires the separate 'loom-server' package to be installed."
            ) from exc
        raise
    return getattr(module, name)


def __dir__() -> list[str]:
    try:
        module = import_module("loom_server.sync_service")
    except ModuleNotFoundError:
        return []
    return sorted(set(module.__dict__))
