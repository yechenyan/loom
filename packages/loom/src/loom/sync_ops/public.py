from __future__ import annotations

from ..server_config import resolve_base_url
from ..workspace_snapshot import list_local_workspaces
from .http import request_json
from .raw import pull_single_raw_workspace
from .workspace import pull_single_workspace, push_single_workspace


def push_workspaces(workspace_root, server_url: str, workspace: str | None = None, message: str | None = None):
    workspaces = (workspace,) if workspace else list_local_workspaces(workspace_root)
    resolved_server_url = resolve_base_url(server_url)
    return tuple(push_single_workspace(workspace_root, resolved_server_url, name, message, request_json) for name in workspaces if name is not None)


def pull_workspaces(workspace_root, server_url: str, workspace: str | None = None):
    resolved_server_url = resolve_base_url(server_url)
    workspaces = (workspace,) if workspace else _list_remote_workspaces(resolved_server_url)
    return tuple(pull_single_workspace(workspace_root, resolved_server_url, name, request_json) for name in workspaces)


def pull_raw_workspaces(workspace_root, server_url: str | None, workspace: str | None = None, *, relative_paths=None):
    resolved_server_url = resolve_base_url(server_url)
    workspaces = (workspace,) if workspace else _list_remote_workspaces(resolved_server_url)
    return tuple(pull_single_raw_workspace(workspace_root, resolved_server_url, name, request_json, relative_paths=relative_paths) for name in workspaces if name is not None)


def _list_remote_workspaces(server_url: str) -> tuple[str, ...]:
    return tuple(str(item["name"]) for item in request_json("GET", f"{server_url.rstrip('/')}/api/workspaces")["workspaces"])
