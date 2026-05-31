from __future__ import annotations

from ..explore_repo import list_scope_commits_since
from ..sync_state import WorkspaceSyncState


def effective_base_revision(state: WorkspaceSyncState) -> str | None:
    return state.pending_rebase_revision or state.last_pulled_revision or state.last_pushed_revision


def effective_file_manifest(state: WorkspaceSyncState) -> dict[str, str] | None:
    return state.pending_rebase_files or state.last_synced_files


def effective_raw_manifest(state: WorkspaceSyncState) -> dict[str, str] | None:
    return state.pending_rebase_raw_files or state.last_synced_raw_files


def has_local_commits(workspace_root, workspace: str, state: WorkspaceSyncState) -> bool:
    if state.pending_rebase_revision:
        return True
    if not state.last_sync_commit:
        return False
    return bool(list_scope_commits_since(workspace_root, workspace, state.last_sync_commit))
