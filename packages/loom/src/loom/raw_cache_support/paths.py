from __future__ import annotations

import os
from pathlib import Path


def resolve_workspace_root(workspace_root: Path | str | None = None) -> Path:
    if workspace_root is not None:
        return Path(workspace_root).resolve()
    return Path(os.environ.get("LOOM_WORKSPACE_ROOT", Path.cwd())).resolve()


def resolve_loom_root(workspace_root: Path | str | None = None) -> Path:
    return resolve_workspace_root(workspace_root) / "test-project" / "loom"


def resolve_cache_root(workspace_root: Path | str | None = None) -> Path:
    return resolve_loom_root(workspace_root) / ".loom"


def resolve_raw_cache_dir(workspace_root: Path | str | None, workspace: str) -> Path:
    return resolve_cache_root(workspace_root) / "raw" / workspace


def resolve_local_raw_workspace_dir(workspace_root: Path | str | None, workspace: str) -> Path:
    return resolve_loom_root(workspace_root) / "loom_raw" / workspace
