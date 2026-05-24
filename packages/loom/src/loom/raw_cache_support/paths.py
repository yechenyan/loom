from __future__ import annotations

import os
from pathlib import Path


def resolve_workspace_root(workspace_root: Path | str | None = None) -> Path:
    if workspace_root is not None:
        return Path(workspace_root).resolve()
    return Path(os.environ.get("LOOM_WORKSPACE_ROOT", Path.cwd())).resolve()


def resolve_loom_root(workspace_root: Path | str | None = None) -> Path:
    return resolve_workspace_root(workspace_root) / "loom"


def resolve_cache_root(workspace_root: Path | str | None = None) -> Path:
    return resolve_loom_root(workspace_root) / ".loom"


def resolve_raw_cache_dir(workspace_root: Path | str | None, workspace: str) -> Path:
    return resolve_cache_root(workspace_root) / "raw" / workspace


def resolve_local_raw_workspace_dir(workspace_root: Path | str | None, workspace: str) -> Path:
    return resolve_loom_root(workspace_root) / "loom_raw" / workspace


def list_local_raw_workspaces(workspace_root: Path | str | None = None) -> tuple[str, ...]:
    raw_root = resolve_loom_root(workspace_root) / "loom_raw"
    if not raw_root.exists():
        return ()
    return tuple(child.name for child in sorted(raw_root.iterdir()) if child.is_dir() and not child.name.startswith("."))
