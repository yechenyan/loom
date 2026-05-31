from __future__ import annotations

from urllib import parse

from ..raw_cache import (
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
from ..workspace_snapshot import decode_snapshot_files
from .models import RawWorkspacePullResult


def normalize_raw_manifest(value: object) -> dict[str, dict[str, str | int]]:
    if not isinstance(value, dict):
        return {}
    return {path: {"sha256": str(item["sha256"]), "size_bytes": int(item.get("size_bytes", 0))} for path, item in value.items() if isinstance(path, str) and isinstance(item, dict) and isinstance(item.get("sha256"), str)}


def raw_hash_manifest(manifest: dict[str, dict[str, str | int]]) -> dict[str, str]:
    return {path: str(item["sha256"]) for path, item in manifest.items()}


def pull_single_raw_workspace(workspace_root, server_url: str, workspace: str, request_json, *, relative_paths=None, only_cached_paths=False, detect_conflicts=False) -> RawWorkspacePullResult:
    response = request_json("GET", f"{server_url.rstrip('/')}/api/workspaces/{parse.quote(workspace)}/raw-manifest")
    manifest = normalize_raw_manifest(response.get("raw_manifest"))
    notice_path = _write_notice_if_needed(workspace_root, workspace, manifest, detect_conflicts)
    selected_paths = _select_paths(workspace_root, workspace, manifest, relative_paths, only_cached_paths)
    state = load_raw_cache_state(workspace_root, workspace)
    deleted_paths = [path for path in (selected_paths if (relative_paths is not None or only_cached_paths) else (state.manifest or {})) if path not in manifest]
    remove_deleted_raw_cache_paths(workspace_root, workspace, deleted_paths)
    downloaded, linked = _materialize_selected_paths(workspace_root, server_url, workspace, manifest, selected_paths, request_json)
    next_manifest = dict(state.manifest or {})
    for path in deleted_paths:
        next_manifest.pop(path, None)
    next_manifest.update(manifest)
    save_raw_cache_state(workspace_root, RawCacheState(workspace=workspace, manifest=next_manifest))
    return RawWorkspacePullResult(workspace=workspace, downloaded_file_count=downloaded, linked_file_count=linked, deleted_file_count=len(deleted_paths), manifest_file_count=len(manifest), raw_conflict_notice_path=notice_path)


def _write_notice_if_needed(workspace_root, workspace: str, manifest, detect_conflicts: bool) -> str | None:
    if not detect_conflicts:
        return None
    notice_path = write_raw_conflict_notice(workspace_root, workspace, detect_local_raw_conflicts(workspace_root, workspace, manifest))
    return str(notice_path) if notice_path else None


def _select_paths(workspace_root, workspace: str, manifest, relative_paths, only_cached_paths: bool):
    if relative_paths is not None:
        missing = [path for path in relative_paths if path not in manifest]
        if missing:
            raise FileNotFoundError(f"Raw paths not found in remote workspace `{workspace}`: {', '.join(missing)}")
        return tuple(relative_paths)
    return list_cached_raw_paths(workspace_root, workspace) if only_cached_paths else tuple(sorted(manifest))


def _materialize_selected_paths(workspace_root, server_url: str, workspace: str, manifest, selected_paths, request_json):
    downloaded = linked = 0
    for relative_path in sorted(path for path in selected_paths if path in manifest):
        item = manifest[relative_path]
        expected_sha256 = str(item["sha256"])
        cached_path = get_cached_raw_path(workspace_root, workspace, relative_path)
        if is_cached_raw_path_current(cached_path, expected_sha256):
            continue
        local_path = populate_raw_cache_from_local_source(workspace_root, workspace, relative_path)
        if local_path is not None and is_cached_raw_path_current(local_path, expected_sha256):
            linked += 1
            continue
        payload = request_json("GET", f"{server_url.rstrip('/')}/api/raw/objects/{parse.quote(expected_sha256)}")
        file_payload = decode_snapshot_files([{"path": relative_path, "sha256": expected_sha256, "content_base64": payload["content_base64"], "size_bytes": int(item["size_bytes"])}])[0]
        write_raw_cache_file(workspace_root, workspace, relative_path, file_payload.content)
        downloaded += 1
    return downloaded, linked
