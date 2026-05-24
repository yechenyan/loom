from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import os
from urllib import error, parse, request

from .explore_repo import (
    confirm_changes,
    get_repo_head_commit,
    get_repo_status,
    list_scope_commits_since,
)
from .raw_cache import (
    RawCacheState,
    detect_local_raw_conflicts,
    get_cached_raw_path,
    is_cached_raw_path_current,
    list_cached_raw_paths,
    load_raw_cache_state,
    populate_raw_cache_from_local_source,
    remove_deleted_raw_cache_paths,
    save_raw_cache_state,
    write_raw_cache_file,
    write_raw_conflict_notice,
)
from .raw_snapshot import (
    build_raw_manifest,
    build_raw_workspace_delta,
    build_raw_workspace_snapshot,
    encode_raw_files,
)
from .sync_state import WorkspaceSyncState, load_workspace_sync_state, save_workspace_sync_state
from .workspace_merge import merge_workspace_snapshots
from .workspace_snapshot import (
    WorkspaceSnapshot,
    apply_workspace_delta,
    build_snapshot_manifest,
    build_workspace_delta,
    build_workspace_snapshot,
    build_workspace_snapshot_from_commit,
    decode_snapshot_files,
    encode_workspace_files,
    list_local_workspaces,
)


@dataclass(frozen=True)
class WorkspacePushResult:
    workspace: str
    revision_id: str | None
    tree_hash: str | None
    changed_file_count: int
    deleted_file_count: int
    raw_uploaded_object_count: int
    raw_mapping_changed_count: int
    raw_mapping_deleted_count: int
    conflicted: bool = False
    conflict_paths: tuple[str, ...] = ()
    raw_conflict_notice_path: str | None = None


@dataclass(frozen=True)
class WorkspacePullResult:
    workspace: str
    revision_id: str
    changed: bool
    changed_file_count: int
    deleted_file_count: int
    conflicted: bool = False
    conflict_paths: tuple[str, ...] = ()
    raw_conflict_notice_path: str | None = None


@dataclass(frozen=True)
class RawWorkspacePullResult:
    workspace: str
    downloaded_file_count: int
    linked_file_count: int
    deleted_file_count: int
    manifest_file_count: int
    raw_conflict_notice_path: str | None = None


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

    state = load_workspace_sync_state(workspace_root, workspace)
    remote_head = _get_remote_workspace_head(server_url, workspace)
    remote_revision = str(remote_head.get("head_revision_id") or "")

    if state.pending_rebase_revision and remote_revision and remote_revision != state.pending_rebase_revision:
        raise RuntimeError(
            f"Workspace `{workspace}` still has a pending rebase onto revision "
            f"`{state.pending_rebase_revision}`, but the remote head already moved to `{remote_revision}`. "
            "Please run `loom pull <workspace>` first."
        )

    if remote_revision and remote_revision != _effective_base_revision(state):
        rebase_result = _pull_single_workspace(workspace_root, server_url, workspace)
        if rebase_result.conflicted:
            return WorkspacePushResult(
                workspace=workspace,
                revision_id=rebase_result.revision_id,
                tree_hash=None,
                changed_file_count=rebase_result.changed_file_count,
                deleted_file_count=rebase_result.deleted_file_count,
                raw_uploaded_object_count=0,
                raw_mapping_changed_count=0,
                raw_mapping_deleted_count=0,
                conflicted=True,
                conflict_paths=rebase_result.conflict_paths,
                raw_conflict_notice_path=rebase_result.raw_conflict_notice_path,
            )
        state = load_workspace_sync_state(workspace_root, workspace)

    snapshot = build_workspace_snapshot(workspace_root, workspace)
    raw_snapshot = build_raw_workspace_snapshot(workspace_root, workspace)
    current_commit = get_repo_head_commit(workspace_root)

    base_revision = _effective_base_revision(state)
    previous_files_manifest = _effective_file_manifest(state)
    previous_raw_manifest = _effective_raw_manifest(state)
    delta = build_workspace_delta(snapshot, previous_files_manifest)
    raw_delta = build_raw_workspace_delta(raw_snapshot, previous_raw_manifest)

    raw_uploaded_object_count = _upload_missing_raw_objects(server_url, raw_delta.changed_files)
    payload = {
        "base_revision": base_revision,
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

    updated_state = WorkspaceSyncState(
        workspace=workspace,
        last_pulled_revision=str(response["revision_id"]),
        last_pushed_revision=str(response["revision_id"]),
        last_synced_tree_hash=snapshot.tree_hash,
        last_sync_commit=current_commit,
        last_synced_files=build_snapshot_manifest(snapshot),
        last_synced_raw_files=build_raw_manifest(raw_snapshot),
    )
    save_workspace_sync_state(workspace_root, updated_state)

    raw_refresh = _pull_single_raw_workspace(
        workspace_root,
        server_url,
        workspace,
        only_cached_paths=True,
        detect_conflicts=True,
    )

    return WorkspacePushResult(
        workspace=workspace,
        revision_id=str(response["revision_id"]),
        tree_hash=snapshot.tree_hash,
        changed_file_count=int(response.get("changed_file_count", len(delta.changed_files))),
        deleted_file_count=int(response.get("deleted_file_count", len(delta.deleted_paths))),
        raw_uploaded_object_count=raw_uploaded_object_count,
        raw_mapping_changed_count=int(response.get("raw_mapping_changed_count", len(raw_delta.changed_files))),
        raw_mapping_deleted_count=int(response.get("raw_mapping_deleted_count", len(raw_delta.deleted_paths))),
        raw_conflict_notice_path=raw_refresh.raw_conflict_notice_path,
    )


def _pull_single_workspace(workspace_root: Path | str, server_url: str, workspace: str) -> WorkspacePullResult:
    state = load_workspace_sync_state(workspace_root, workspace)
    local_snapshot = build_workspace_snapshot(workspace_root, workspace)
    base_revision = _effective_base_revision(state)

    response = _request_json("GET", _build_pull_url(server_url, workspace, base_revision))
    remote_tree_hash = str(response["tree_hash"])
    remote_revision = str(response["revision_id"])
    remote_raw_manifest = _normalize_raw_manifest(response.get("raw_manifest"))
    remote_raw_hash_manifest = _raw_hash_manifest(remote_raw_manifest)

    if local_snapshot.tree_hash == remote_tree_hash and state.last_pulled_revision == remote_revision:
        raw_refresh = _pull_single_raw_workspace(
            workspace_root,
            server_url,
            workspace,
            only_cached_paths=True,
            detect_conflicts=True,
        )
        return WorkspacePullResult(
            workspace=workspace,
            revision_id=remote_revision,
            changed=False,
            changed_file_count=0,
            deleted_file_count=0,
            raw_conflict_notice_path=raw_refresh.raw_conflict_notice_path,
        )

    has_local_commits = _has_local_commits(workspace_root, workspace, state)
    if state.pending_rebase_revision and remote_revision != state.pending_rebase_revision:
        raise RuntimeError(
            f"Workspace `{workspace}` has pending conflict resolution for revision "
            f"`{state.pending_rebase_revision}`, but the remote head already moved to `{remote_revision}`. "
            "Please resolve the local workspace, confirm it, then pull again."
        )

    if not has_local_commits:
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
            last_synced_raw_files=remote_raw_hash_manifest,
        )
        save_workspace_sync_state(workspace_root, updated_state)
        raw_refresh = _pull_single_raw_workspace(
            workspace_root,
            server_url,
            workspace,
            only_cached_paths=True,
            detect_conflicts=True,
        )
        return WorkspacePullResult(
            workspace=workspace,
            revision_id=remote_revision,
            changed=True,
            changed_file_count=int(response.get("changed_file_count", len(files))),
            deleted_file_count=int(response.get("deleted_file_count", len(deleted_paths))),
            raw_conflict_notice_path=raw_refresh.raw_conflict_notice_path,
        )

    base_snapshot = _build_base_snapshot(workspace_root, workspace, state)
    remote_snapshot = _build_remote_snapshot(workspace, base_snapshot, response)
    merged = merge_workspace_snapshots(
        workspace=workspace,
        base=base_snapshot,
        local=local_snapshot,
        remote=remote_snapshot,
    )

    apply_workspace_delta(workspace_root, workspace, merged.files, merged.deleted_paths)
    changed_count = len(merged.files)
    deleted_count = len(merged.deleted_paths)

    if merged.conflict_paths:
        conflict_state = WorkspaceSyncState(
            workspace=workspace,
            last_pulled_revision=state.last_pulled_revision,
            last_pushed_revision=state.last_pushed_revision,
            last_synced_tree_hash=state.last_synced_tree_hash,
            last_sync_commit=state.last_sync_commit,
            last_synced_files=state.last_synced_files,
            last_synced_raw_files=state.last_synced_raw_files,
            pending_rebase_revision=remote_revision,
            pending_rebase_tree_hash=remote_tree_hash,
            pending_rebase_files=build_snapshot_manifest(remote_snapshot),
            pending_rebase_raw_files=remote_raw_hash_manifest,
        )
        save_workspace_sync_state(workspace_root, conflict_state)
        return WorkspacePullResult(
            workspace=workspace,
            revision_id=remote_revision,
            changed=True,
            changed_file_count=changed_count,
            deleted_file_count=deleted_count,
            conflicted=True,
            conflict_paths=merged.conflict_paths,
        )

    commit_hash = confirm_changes(
        workspace_root,
        workspace,
        message=f"Rebase workspace {workspace} onto server revision {remote_revision}",
    )
    updated_snapshot = build_workspace_snapshot(workspace_root, workspace)
    updated_state = WorkspaceSyncState(
        workspace=workspace,
        last_pulled_revision=remote_revision,
        last_pushed_revision=state.last_pushed_revision,
        last_synced_tree_hash=remote_tree_hash,
        last_sync_commit=commit_hash or get_repo_head_commit(workspace_root),
        last_synced_files=build_snapshot_manifest(updated_snapshot),
        last_synced_raw_files=remote_raw_hash_manifest,
        pending_rebase_revision=remote_revision,
        pending_rebase_tree_hash=remote_tree_hash,
        pending_rebase_files=build_snapshot_manifest(remote_snapshot),
        pending_rebase_raw_files=remote_raw_hash_manifest,
    )
    save_workspace_sync_state(workspace_root, updated_state)
    raw_refresh = _pull_single_raw_workspace(
        workspace_root,
        server_url,
        workspace,
        only_cached_paths=True,
        detect_conflicts=True,
    )
    return WorkspacePullResult(
        workspace=workspace,
        revision_id=remote_revision,
        changed=True,
        changed_file_count=changed_count,
        deleted_file_count=deleted_count,
        raw_conflict_notice_path=raw_refresh.raw_conflict_notice_path,
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
    only_cached_paths: bool = False,
    detect_conflicts: bool = False,
) -> RawWorkspacePullResult:
    response = _request_json(
        "GET",
        f"{server_url.rstrip('/')}/api/workspaces/{parse.quote(workspace)}/raw-manifest",
    )
    manifest = _normalize_raw_manifest(response.get("raw_manifest"))

    raw_conflict_notice_path: str | None = None
    if detect_conflicts:
        conflicts = detect_local_raw_conflicts(workspace_root, workspace, manifest)
        notice_path = write_raw_conflict_notice(workspace_root, workspace, conflicts)
        raw_conflict_notice_path = str(notice_path) if notice_path else None

    if relative_paths is not None:
        missing = [path for path in relative_paths if path not in manifest]
        if missing:
            raise FileNotFoundError(f"Raw paths not found in remote workspace `{workspace}`: {', '.join(missing)}")
        selected_paths = tuple(relative_paths)
    elif only_cached_paths:
        selected_paths = list_cached_raw_paths(workspace_root, workspace)
    else:
        selected_paths = tuple(sorted(manifest))

    if relative_paths is not None:
        selected_manifest = {path: manifest[path] for path in selected_paths}
    else:
        selected_manifest = {path: manifest[path] for path in selected_paths if path in manifest}

    state = load_raw_cache_state(workspace_root, workspace)
    previous_manifest = state.manifest or {}
    if relative_paths is not None or only_cached_paths:
        deleted_paths = [path for path in selected_paths if path not in manifest]
    else:
        deleted_paths = [path for path in previous_manifest if path not in manifest]
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
        raw_conflict_notice_path=raw_conflict_notice_path,
    )


def _build_remote_snapshot(
    workspace: str,
    base_snapshot: WorkspaceSnapshot,
    response: dict[str, object],
) -> WorkspaceSnapshot:
    file_map = {item.path: item for item in base_snapshot.files}
    for deleted_path in tuple(str(path) for path in response.get("deleted_paths", [])):
        file_map.pop(deleted_path, None)
    for file_snapshot in decode_snapshot_files(list(response["files"])):
        file_map[file_snapshot.path] = file_snapshot
    files = tuple(file_map[path] for path in sorted(file_map))
    return WorkspaceSnapshot(workspace=workspace, files=files, tree_hash=str(response["tree_hash"]))


def _build_base_snapshot(workspace_root: Path | str, workspace: str, state: WorkspaceSyncState) -> WorkspaceSnapshot:
    if state.pending_rebase_revision:
        raise RuntimeError(
            f"Workspace `{workspace}` still has a pending rebase onto revision `{state.pending_rebase_revision}`. "
            "Resolve the conflict, run `loom confirm`, then `loom push`."
        )
    return build_workspace_snapshot_from_commit(workspace_root, workspace, state.last_sync_commit)


def _effective_base_revision(state: WorkspaceSyncState) -> str | None:
    return state.pending_rebase_revision or state.last_pulled_revision or state.last_pushed_revision


def _effective_file_manifest(state: WorkspaceSyncState) -> dict[str, str] | None:
    return state.pending_rebase_files or state.last_synced_files


def _effective_raw_manifest(state: WorkspaceSyncState) -> dict[str, str] | None:
    return state.pending_rebase_raw_files or state.last_synced_raw_files


def _has_local_commits(workspace_root: Path | str, workspace: str, state: WorkspaceSyncState) -> bool:
    if state.pending_rebase_revision:
        return True
    if not state.last_sync_commit:
        return False
    return bool(list_scope_commits_since(workspace_root, workspace, state.last_sync_commit))


def _get_remote_workspace_head(server_url: str, workspace: str) -> dict[str, object]:
    response = _request_json("GET", f"{server_url.rstrip('/')}/api/workspaces")
    for item in response.get("workspaces", []):
        if isinstance(item, dict) and str(item.get("name")) == workspace:
            return {
                "workspace": workspace,
                "head_revision_id": item.get("head_revision_id"),
            }
    return {"workspace": workspace, "head_revision_id": None}


def _normalize_raw_manifest(value: object) -> dict[str, dict[str, str | int]]:
    if not isinstance(value, dict):
        return {}
    manifest: dict[str, dict[str, str | int]] = {}
    for path, item in value.items():
        if isinstance(path, str) and isinstance(item, dict) and isinstance(item.get("sha256"), str):
            manifest[path] = {
                "sha256": str(item["sha256"]),
                "size_bytes": int(item.get("size_bytes", 0)),
            }
    return manifest


def _raw_hash_manifest(manifest: dict[str, dict[str, str | int]]) -> dict[str, str]:
    return {path: str(item["sha256"]) for path, item in manifest.items()}


def _upload_missing_raw_objects(server_url: str, changed_files: tuple[object, ...]) -> int:
    if not changed_files:
        return 0
    unique_changed_hashes = sorted({file_snapshot.sha256 for file_snapshot in changed_files})
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
        for file_snapshot in changed_files
        if file_snapshot.sha256 in missing_hashes
    ]
    deduped_objects: dict[str, dict[str, object]] = {}
    for payload_item in missing_objects:
        deduped_objects[str(payload_item["sha256"])] = payload_item
    if not deduped_objects:
        return 0
    upload_response = _request_json(
        "POST",
        f"{server_url.rstrip('/')}/api/raw/objects",
        {"objects": list(deduped_objects.values())},
    )
    return int(upload_response.get("stored_count", len(deduped_objects)))


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
