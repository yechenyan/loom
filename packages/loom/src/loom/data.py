from __future__ import annotations

from pathlib import Path

from .raw_cache import (
    get_cached_raw_path,
    is_cached_raw_path_healthy,
    populate_raw_cache_from_local_source,
    resolve_workspace_root,
)
from .sync_client import pull_raw_workspaces


def get(resource: str, *, workspace_root: Path | str | None = None, server_url: str | None = None) -> Path:
    workspace, relative_path = _parse_resource(resource)
    root = resolve_workspace_root(workspace_root)
    cached_path = get_cached_raw_path(root, workspace, relative_path)
    if is_cached_raw_path_healthy(cached_path):
        return cached_path

    local_path = populate_raw_cache_from_local_source(root, workspace, relative_path)
    if local_path is not None and is_cached_raw_path_healthy(local_path):
        return local_path

    result = pull_raw_workspaces(root, server_url, workspace=workspace, relative_paths=(relative_path,))
    if not result or result[0].downloaded_file_count < 0:
        raise FileNotFoundError(f"Resource `{resource}` was not found in local cache or remote workspace.")

    cached_path = get_cached_raw_path(root, workspace, relative_path)
    if not is_cached_raw_path_healthy(cached_path):
        raise FileNotFoundError(f"Resource `{resource}` was not materialized into the local cache.")
    return cached_path


def pull(workspace: str | None = None, *, workspace_root: Path | str | None = None, server_url: str | None = None):
    return pull_raw_workspaces(resolve_workspace_root(workspace_root), server_url, workspace=workspace)


def _parse_resource(resource: str) -> tuple[str, str]:
    normalized = resource.strip().strip("/")
    workspace, separator, relative_path = normalized.partition("/")
    if not separator or not workspace or not relative_path:
        raise ValueError("Resource must use the form `workspace/path/to/file`.")
    return workspace, relative_path
