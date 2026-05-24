from __future__ import annotations

from urllib import parse

from ..explore_repo import confirm_changes, get_repo_head_commit, get_repo_status
from ..raw_snapshot import build_raw_manifest, build_raw_workspace_delta, build_raw_workspace_snapshot, encode_raw_files
from ..sync_state import WorkspaceSyncState, load_workspace_sync_state, save_workspace_sync_state
from ..workspace_merge import merge_workspace_snapshots
from ..workspace_snapshot import WorkspaceSnapshot, apply_workspace_delta, build_snapshot_manifest, build_workspace_delta, build_workspace_snapshot, build_workspace_snapshot_from_commit, decode_snapshot_files, encode_workspace_files
from .models import WorkspacePullResult, WorkspacePushResult
from .raw import pull_single_raw_workspace, raw_hash_manifest
from .state import effective_base_revision, effective_file_manifest, effective_raw_manifest, has_local_commits


def push_single_workspace(workspace_root, server_url: str, workspace: str, message: str | None, request_json) -> WorkspacePushResult:
    if get_repo_status(workspace_root, workspace).entries:
        confirm_changes(workspace_root, workspace, message=f"Auto-confirm workspace {workspace} before push")
    state = load_workspace_sync_state(workspace_root, workspace)
    remote_revision = str(get_remote_workspace_head(server_url, workspace, request_json).get("head_revision_id") or "")
    if remote_revision and remote_revision != effective_base_revision(state):
        pull_result = pull_single_workspace(workspace_root, server_url, workspace, request_json)
        if pull_result.conflicted:
            return WorkspacePushResult(workspace=workspace, revision_id=pull_result.revision_id, tree_hash=None, changed_file_count=pull_result.changed_file_count, deleted_file_count=pull_result.deleted_file_count, raw_uploaded_object_count=0, raw_mapping_changed_count=0, raw_mapping_deleted_count=0, conflicted=True, conflict_paths=pull_result.conflict_paths, raw_conflict_notice_path=pull_result.raw_conflict_notice_path)
        state = load_workspace_sync_state(workspace_root, workspace)
    return _push_snapshot(workspace_root, server_url, workspace, message, state, request_json)


def pull_single_workspace(workspace_root, server_url: str, workspace: str, request_json) -> WorkspacePullResult:
    state = load_workspace_sync_state(workspace_root, workspace)
    local_snapshot = build_workspace_snapshot(workspace_root, workspace)
    response = request_json("GET", build_pull_url(server_url, workspace, effective_base_revision(state)))
    remote_revision = str(response["revision_id"])
    remote_tree_hash = str(response["tree_hash"])
    remote_raw_manifest = raw_hash_manifest(response.get("raw_manifest") if isinstance(response.get("raw_manifest"), dict) else {})
    if local_snapshot.tree_hash == remote_tree_hash and state.last_pulled_revision == remote_revision:
        refresh = pull_single_raw_workspace(workspace_root, server_url, workspace, request_json, only_cached_paths=True, detect_conflicts=True)
        return WorkspacePullResult(workspace=workspace, revision_id=remote_revision, changed=False, changed_file_count=0, deleted_file_count=0, raw_conflict_notice_path=refresh.raw_conflict_notice_path)
    return _fast_forward(workspace_root, server_url, workspace, state, response, request_json, remote_revision, remote_tree_hash, remote_raw_manifest) if not has_local_commits(workspace_root, workspace, state) else _rebase(workspace_root, server_url, workspace, state, local_snapshot, response, request_json, remote_revision, remote_tree_hash, remote_raw_manifest)


def get_remote_workspace_head(server_url: str, workspace: str, request_json):
    response = request_json("GET", f"{server_url.rstrip('/')}/api/workspaces")
    for item in response.get("workspaces", []):
        if isinstance(item, dict) and str(item.get("name")) == workspace:
            return {"workspace": workspace, "head_revision_id": item.get("head_revision_id")}
    return {"workspace": workspace, "head_revision_id": None}


def upload_missing_raw_objects(server_url: str, changed_files, request_json) -> int:
    if not changed_files:
        return 0
    hashes = sorted({file_snapshot.sha256 for file_snapshot in changed_files})
    missing = {str(item) for item in request_json("POST", f"{server_url.rstrip('/')}/api/raw/exists", {"hashes": hashes}).get("missing_hashes", [])}
    objects = {file.sha256: {"sha256": file.sha256, "size_bytes": file.size_bytes, "content_base64": encode_raw_files([file])[0]["content_base64"]} for file in changed_files if file.sha256 in missing}
    if not objects:
        return 0
    return int(request_json("POST", f"{server_url.rstrip('/')}/api/raw/objects", {"objects": list(objects.values())}).get("stored_count", len(objects)))


def build_pull_url(server_url: str, workspace: str, base_revision: str | None) -> str:
    base_url = f"{server_url.rstrip('/')}/api/workspaces/{parse.quote(workspace)}/pull"
    return base_url if not base_revision else f"{base_url}?base_revision={parse.quote(base_revision)}"


def _push_snapshot(workspace_root, server_url, workspace, message, state, request_json):
    snapshot = build_workspace_snapshot(workspace_root, workspace)
    raw_snapshot = build_raw_workspace_snapshot(workspace_root, workspace)
    delta = build_workspace_delta(snapshot, effective_file_manifest(state))
    raw_delta = build_raw_workspace_delta(raw_snapshot, effective_raw_manifest(state))
    uploaded = upload_missing_raw_objects(server_url, raw_delta.changed_files, request_json)
    response = request_json("POST", f"{server_url.rstrip('/')}/api/workspaces/{parse.quote(workspace)}/push", {"base_revision": effective_base_revision(state), "local_commit": get_repo_head_commit(workspace_root), "tree_hash": snapshot.tree_hash, "message": message or f"Push workspace {workspace}", "files": encode_workspace_files(delta.changed_files), "deleted_paths": list(delta.deleted_paths), "raw_files": [{"path": file.path, "sha256": file.sha256, "size_bytes": file.size_bytes, "content_base64": ""} for file in raw_delta.changed_files], "raw_deleted_paths": list(raw_delta.deleted_paths)})
    save_workspace_sync_state(workspace_root, WorkspaceSyncState(workspace=workspace, last_pulled_revision=str(response["revision_id"]), last_pushed_revision=str(response["revision_id"]), last_synced_tree_hash=snapshot.tree_hash, last_sync_commit=get_repo_head_commit(workspace_root), last_synced_files=build_snapshot_manifest(snapshot), last_synced_raw_files=build_raw_manifest(raw_snapshot)))
    refresh = pull_single_raw_workspace(workspace_root, server_url, workspace, request_json, only_cached_paths=True, detect_conflicts=True)
    return WorkspacePushResult(workspace=workspace, revision_id=str(response["revision_id"]), tree_hash=snapshot.tree_hash, changed_file_count=int(response.get("changed_file_count", len(delta.changed_files))), deleted_file_count=int(response.get("deleted_file_count", len(delta.deleted_paths))), raw_uploaded_object_count=uploaded, raw_mapping_changed_count=int(response.get("raw_mapping_changed_count", len(raw_delta.changed_files))), raw_mapping_deleted_count=int(response.get("raw_mapping_deleted_count", len(raw_delta.deleted_paths))), raw_conflict_notice_path=refresh.raw_conflict_notice_path)


def _fast_forward(workspace_root, server_url, workspace, state, response, request_json, remote_revision, remote_tree_hash, remote_raw_manifest):
    files = decode_snapshot_files(list(response["files"]))
    deleted_paths = tuple(str(path) for path in response.get("deleted_paths", []))
    apply_workspace_delta(workspace_root, workspace, files, deleted_paths)
    commit_hash = confirm_changes(workspace_root, workspace, message=f"Pull workspace {workspace} from server revision {remote_revision}")
    updated_snapshot = build_workspace_snapshot(workspace_root, workspace)
    save_workspace_sync_state(workspace_root, WorkspaceSyncState(workspace=workspace, last_pulled_revision=remote_revision, last_pushed_revision=state.last_pushed_revision, last_synced_tree_hash=remote_tree_hash, last_sync_commit=commit_hash or get_repo_head_commit(workspace_root), last_synced_files=build_snapshot_manifest(updated_snapshot), last_synced_raw_files=remote_raw_manifest))
    refresh = pull_single_raw_workspace(workspace_root, server_url, workspace, request_json, only_cached_paths=True, detect_conflicts=True)
    return WorkspacePullResult(workspace=workspace, revision_id=remote_revision, changed=True, changed_file_count=int(response.get("changed_file_count", len(files))), deleted_file_count=int(response.get("deleted_file_count", len(deleted_paths))), raw_conflict_notice_path=refresh.raw_conflict_notice_path)


def _rebase(workspace_root, server_url, workspace, state, local_snapshot, response, request_json, remote_revision, remote_tree_hash, remote_raw_manifest):
    base_snapshot = build_workspace_snapshot_from_commit(workspace_root, workspace, state.last_sync_commit)
    remote_snapshot = build_remote_snapshot(workspace, base_snapshot, response)
    merged = merge_workspace_snapshots(workspace=workspace, base=base_snapshot, local=local_snapshot, remote=remote_snapshot)
    apply_workspace_delta(workspace_root, workspace, merged.files, merged.deleted_paths)
    if merged.conflict_paths:
        save_workspace_sync_state(workspace_root, WorkspaceSyncState(workspace=workspace, last_pulled_revision=state.last_pulled_revision, last_pushed_revision=state.last_pushed_revision, last_synced_tree_hash=state.last_synced_tree_hash, last_sync_commit=state.last_sync_commit, last_synced_files=state.last_synced_files, last_synced_raw_files=state.last_synced_raw_files, pending_rebase_revision=remote_revision, pending_rebase_tree_hash=remote_tree_hash, pending_rebase_files=build_snapshot_manifest(remote_snapshot), pending_rebase_raw_files=remote_raw_manifest))
        return WorkspacePullResult(workspace=workspace, revision_id=remote_revision, changed=True, changed_file_count=len(merged.files), deleted_file_count=len(merged.deleted_paths), conflicted=True, conflict_paths=merged.conflict_paths)
    commit_hash = confirm_changes(workspace_root, workspace, message=f"Rebase workspace {workspace} onto server revision {remote_revision}")
    updated_snapshot = build_workspace_snapshot(workspace_root, workspace)
    save_workspace_sync_state(workspace_root, WorkspaceSyncState(workspace=workspace, last_pulled_revision=remote_revision, last_pushed_revision=state.last_pushed_revision, last_synced_tree_hash=remote_tree_hash, last_sync_commit=commit_hash or get_repo_head_commit(workspace_root), last_synced_files=build_snapshot_manifest(updated_snapshot), last_synced_raw_files=remote_raw_manifest, pending_rebase_revision=remote_revision, pending_rebase_tree_hash=remote_tree_hash, pending_rebase_files=build_snapshot_manifest(remote_snapshot), pending_rebase_raw_files=remote_raw_manifest))
    refresh = pull_single_raw_workspace(workspace_root, server_url, workspace, request_json, only_cached_paths=True, detect_conflicts=True)
    return WorkspacePullResult(workspace=workspace, revision_id=remote_revision, changed=True, changed_file_count=len(merged.files), deleted_file_count=len(merged.deleted_paths), raw_conflict_notice_path=refresh.raw_conflict_notice_path)


def build_remote_snapshot(workspace: str, base_snapshot: WorkspaceSnapshot, response: dict[str, object]) -> WorkspaceSnapshot:
    file_map = {item.path: item for item in base_snapshot.files}
    for deleted_path in tuple(str(path) for path in response.get("deleted_paths", [])):
        file_map.pop(deleted_path, None)
    for file_snapshot in decode_snapshot_files(list(response["files"])):
        file_map[file_snapshot.path] = file_snapshot
    return WorkspaceSnapshot(workspace=workspace, files=tuple(file_map[path] for path in sorted(file_map)), tree_hash=str(response["tree_hash"]))
