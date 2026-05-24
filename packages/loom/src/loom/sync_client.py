from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import os
from urllib import error, parse, request

from .explore_repo import confirm_changes, get_repo_head_commit, get_repo_status
from .raw_snapshot import (
    build_raw_manifest,
    build_raw_workspace_delta,
    build_raw_workspace_snapshot,
    encode_raw_files,
)
from .sync_state import WorkspaceSyncState, load_workspace_sync_state, save_workspace_sync_state
from .workspace_snapshot import (
    apply_workspace_delta,
    build_snapshot_manifest,
    build_workspace_delta,
    build_workspace_snapshot,
    decode_snapshot_files,
    encode_workspace_files,
    list_local_workspaces,
)
from .raw_cache import (
    RawCacheState,
    get_cached_raw_path,
    is_cached_raw_path_current,
    is_cached_raw_path_healthy,
    load_raw_cache_state,
    populate_raw_cache_from_local_source,
    remove_deleted_raw_cache_paths,
    save_raw_cache_state,
    write_raw_cache_file,
)


@dataclass(frozen=True)
class WorkspacePushResult:
    workspace: str
    revision_id: str
    tree_hash: str
    changed_file_count: int
    deleted_file_count: int
    raw_uploaded_object_count: int
    raw_mapping_changed_count: int
    raw_mapping_deleted_count: int


@dataclass(frozen=True)
class WorkspacePullResult:
    workspace: str
    revision_id: str
    changed: bool
    changed_file_count: int
    deleted_file_count: int


@dataclass(frozen=True)
class RawWorkspacePullResult:
    workspace: str
    downloaded_file_count: int
    linked_file_count: int
    deleted_file_count: int
    manifest_file_count: int


def push_workspaces(
    workspace_root: Path | str,
    server_url: str,
    workspace: str | None = None,
    message: str | None = None,
) -> tuple[WorkspacePushResult, ...]:
    workspaces = (workspace,) if workspace else list_local_workspaces(workspace_root)
    results: list[WorkspacePushResult] = []
    for workspace_name in workspaces:
        if workspace_name is None:
            continue
        results.append(_push_single_workspace(workspace_root, server_url, workspace_name, message))
    return tuple(results)


def pull_workspaces(
    workspace_root: Path | str,
    server_url: str,
    workspace: str | None = None,
) -> tuple[WorkspacePullResult, ...]:
    workspaces = (workspace,) if workspace else _list_remote_workspaces(server_url)
    results: list[WorkspacePullResult] = []
    for workspace_name in workspaces:
        results.append(_pull_single_workspace(workspace_root, server_url, workspace_name))
    return tuple(results)


def pull_raw_workspaces(
    workspace_root: Path | str,
    server_url: str | None,
    workspace: str | None = None,
    *,
    relative_paths: tuple[str, ...] | None = None,
) -> tuple[RawWorkspacePullResult, ...]:
    resolved_server_url = server_url or os.environ.get("LOOM_SERVER_URL", "http://127.0.0.1:8765")
    workspaces = (workspace,) if workspace else _list_remote_workspaces(resolved_server_url)
    results: list[RawWorkspacePullResult] = []
    for workspace_name in workspaces:
        if workspace_name is None:
            continue
        results.append(
            _pull_single_raw_workspace(
                workspace_root,
                resolved_server_url,
                workspace_name,
                relative_paths=relative_paths,
            )
        )
    return tuple(results)


def _push_single_workspace(
    workspace_root: Path | str,
    server_url: str,
    workspace: str,
    message: str | None,
) -> WorkspacePushResult:
    status = get_repo_status(workspace_root, workspace)
    if status.entries:
        confirm_changes(
            workspace_root,
            workspace,
            message=f"Auto-confirm workspace {workspace} before push",
        )

    snapshot = build_workspace_snapshot(workspace_root, workspace)
    raw_snapshot = build_raw_workspace_snapshot(workspace_root, workspace)
    state = load_workspace_sync_state(workspace_root, workspace)
    current_commit = get_repo_head_commit(workspace_root)
    delta = build_workspace_delta(snapshot, state.last_synced_files)
    raw_delta = build_raw_workspace_delta(raw_snapshot, state.last_synced_raw_files)
    raw_uploaded_object_count = 0
    if raw_delta.changed_files:
        unique_changed_hashes = sorted({file_snapshot.sha256 for file_snapshot in raw_delta.changed_files})
        missing_hashes_response = _request_json(
            "POST",
            f"{server_url.rstrip('/')}/api/raw/exists",
            {"hashes": unique_changed_hashes},
        )
        missing_hashes = {str(item) for item in missing_hashes_response.get("missing_hashes", [])}
        missing_objects = [
            {
                "sha256": file_snapshot.sha256,
                "size_bytes": file_snapshot.size_bytes,
                "content_base64": encode_raw_files([file_snapshot])[0]["content_base64"],
            }
            for file_snapshot in raw_delta.changed_files
            if file_snapshot.sha256 in missing_hashes
        ]
        deduped_objects: dict[str, dict[str, object]] = {}
        for payload_item in missing_objects:
            deduped_objects[str(payload_item["sha256"])] = payload_item
        if deduped_objects:
            upload_response = _request_json(
                "POST",
                f"{server_url.rstrip('/')}/api/raw/objects",
                {"objects": list(deduped_objects.values())},
            )
            raw_uploaded_object_count = int(upload_response.get("stored_count", len(deduped_objects)))
    payload = {
        "base_revision": state.last_pulled_revision or state.last_pushed_revision,
        "local_commit": current_commit,
        "tree_hash": snapshot.tree_hash,
        "message": message or f"Push workspace {workspace}",
        "files": encode_workspace_files(delta.changed_files),
        "deleted_paths": list(delta.deleted_paths),
        "raw_files": [
            {
                "path": file_snapshot.path,
                "sha256": file_snapshot.sha256,
                "size_bytes": file_snapshot.size_bytes,
                "content_base64": "",
            }
            for file_snapshot in raw_delta.changed_files
        ],
        "raw_deleted_paths": list(raw_delta.deleted_paths),
    }
    response = _request_json(
        "POST",
        f"{server_url.rstrip('/')}/api/workspaces/{parse.quote(workspace)}/push",
        payload,
    )

    state.last_pulled_revision = str(response["revision_id"])
    state.last_pushed_revision = str(response["revision_id"])
    state.last_synced_tree_hash = snapshot.tree_hash
    state.last_sync_commit = current_commit
    state.last_synced_files = build_snapshot_manifest(snapshot)
    state.last_synced_raw_files = build_raw_manifest(raw_snapshot)
    save_workspace_sync_state(workspace_root, state)

    return WorkspacePushResult(
        workspace=workspace,
        revision_id=str(response["revision_id"]),
        tree_hash=snapshot.tree_hash,
        changed_file_count=int(response.get("changed_file_count", len(delta.changed_files))),
        deleted_file_count=int(response.get("deleted_file_count", len(delta.deleted_paths))),
        raw_uploaded_object_count=raw_uploaded_object_count,
        raw_mapping_changed_count=int(response.get("raw_mapping_changed_count", len(raw_delta.changed_files))),
        raw_mapping_deleted_count=int(response.get("raw_mapping_deleted_count", len(raw_delta.deleted_paths))),
    )


def _pull_single_workspace(workspace_root: Path | str, server_url: str, workspace: str) -> WorkspacePullResult:
    state = load_workspace_sync_state(workspace_root, workspace)
    local_snapshot = build_workspace_snapshot(workspace_root, workspace)

    response = _request_json(
        "GET",
        _build_pull_url(server_url, workspace, state.last_pulled_revision or state.last_pushed_revision),
    )
    remote_tree_hash = str(response["tree_hash"])
    remote_revision = str(response["revision_id"])
    if local_snapshot.tree_hash == remote_tree_hash and state.last_pulled_revision == remote_revision:
        return WorkspacePullResult(
            workspace=workspace,
            revision_id=remote_revision,
            changed=False,
            changed_file_count=0,
            deleted_file_count=0,
        )

    files = decode_snapshot_files(list(response["files"]))
    deleted_paths = tuple(str(path) for path in response.get("deleted_paths", []))
    apply_workspace_delta(workspace_root, workspace, files, deleted_paths)
    updated_snapshot = build_workspace_snapshot(workspace_root, workspace)
    commit_hash = confirm_changes(
        workspace_root,
        workspace,
        message=f"Pull workspace {workspace} from server revision {remote_revision}",
    )

    updated_state = WorkspaceSyncState(
        workspace=workspace,
        last_pulled_revision=remote_revision,
        last_pushed_revision=state.last_pushed_revision,
        last_synced_tree_hash=remote_tree_hash,
        last_sync_commit=commit_hash or get_repo_head_commit(workspace_root),
        last_synced_files=build_snapshot_manifest(updated_snapshot),
        last_synced_raw_files={
            str(path): str(item["sha256"])
            for path, item in dict(response.get("raw_manifest", {})).items()
            if isinstance(path, str) and isinstance(item, dict) and "sha256" in item
        },
    )
    save_workspace_sync_state(workspace_root, updated_state)

    return WorkspacePullResult(
        workspace=workspace,
        revision_id=remote_revision,
        changed=True,
        changed_file_count=int(response.get("changed_file_count", len(files))),
        deleted_file_count=int(response.get("deleted_file_count", len(deleted_paths))),
    )


def _list_remote_workspaces(server_url: str) -> tuple[str, ...]:
    response = _request_json("GET", f"{server_url.rstrip('/')}/api/workspaces")
    workspaces = [str(item["name"]) for item in response["workspaces"]]
    return tuple(workspaces)


def _pull_single_raw_workspace(
    workspace_root: Path | str,
    server_url: str,
    workspace: str,
    *,
    relative_paths: tuple[str, ...] | None = None,
) -> RawWorkspacePullResult:
    response = _request_json(
        "GET",
        f"{server_url.rstrip('/')}/api/workspaces/{parse.quote(workspace)}/raw-manifest",
    )
    manifest = {
        str(path): {
            "sha256": str(item["sha256"]),
            "size_bytes": int(item["size_bytes"]),
        }
        for path, item in dict(response.get("raw_manifest", {})).items()
        if isinstance(path, str) and isinstance(item, dict)
    }
    if relative_paths is not None:
        missing = [path for path in relative_paths if path not in manifest]
        if missing:
            raise FileNotFoundError(f"Raw paths not found in remote workspace `{workspace}`: {', '.join(missing)}")
        selected_manifest = {path: manifest[path] for path in relative_paths}
    else:
        selected_manifest = manifest

    state = load_raw_cache_state(workspace_root, workspace)
    previous_manifest = state.manifest or {}
    deleted_paths = [
        path for path in previous_manifest
        if path not in manifest and (relative_paths is None or path in relative_paths)
    ]
    remove_deleted_raw_cache_paths(workspace_root, workspace, deleted_paths)

    downloaded_file_count = 0
    linked_file_count = 0
    for relative_path, item in sorted(selected_manifest.items()):
        cached_path = get_cached_raw_path(workspace_root, workspace, relative_path)
        expected_sha256 = str(item["sha256"])
        if is_cached_raw_path_current(cached_path, expected_sha256):
            continue
        local_path = populate_raw_cache_from_local_source(workspace_root, workspace, relative_path)
        if local_path is not None and is_cached_raw_path_current(local_path, expected_sha256):
            linked_file_count += 1
            continue
        object_payload = _request_json(
            "GET",
            f"{server_url.rstrip('/')}/api/raw/objects/{parse.quote(expected_sha256)}",
        )
        content_base64 = object_payload.get("content_base64")
        if not isinstance(content_base64, str):
            raise RuntimeError(f"Raw object `{expected_sha256}` response is missing content.")
        file_payload = decode_snapshot_files(
            [
                {
                    "path": relative_path,
                    "sha256": expected_sha256,
                    "content_base64": content_base64,
                    "size_bytes": int(item["size_bytes"]),
                }
            ]
        )[0]
        write_raw_cache_file(workspace_root, workspace, relative_path, file_payload.content)
        downloaded_file_count += 1

    next_manifest = dict(previous_manifest)
    for path in deleted_paths:
        next_manifest.pop(path, None)
    next_manifest.update(manifest)
    save_raw_cache_state(workspace_root, RawCacheState(workspace=workspace, manifest=next_manifest))

    return RawWorkspacePullResult(
        workspace=workspace,
        downloaded_file_count=downloaded_file_count,
        linked_file_count=linked_file_count,
        deleted_file_count=len(deleted_paths),
        manifest_file_count=len(manifest),
    )


def _build_pull_url(server_url: str, workspace: str, base_revision: str | None) -> str:
    base_url = f"{server_url.rstrip('/')}/api/workspaces/{parse.quote(workspace)}/pull"
    if not base_revision:
        return base_url
    return f"{base_url}?{parse.urlencode({'base_revision': base_revision})}"


def _request_json(method: str, url: str, payload: dict[str, object] | None = None) -> dict[str, object]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    http_request = request.Request(url, data=data, method=method, headers=headers)
    try:
        with request.urlopen(http_request) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exception:
        detail = exception.read().decode("utf-8")
        raise RuntimeError(f"Server request failed ({exception.code}): {detail}") from exception
