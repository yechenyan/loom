from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from .raw_cache import resolve_cache_root


@dataclass
class WorkspaceSyncState:
    workspace: str
    last_pulled_revision: str | None = None
    last_pushed_revision: str | None = None
    last_synced_tree_hash: str | None = None
    last_sync_commit: str | None = None
    last_synced_files: dict[str, str] | None = None
    last_synced_raw_files: dict[str, str] | None = None
    pending_rebase_revision: str | None = None
    pending_rebase_tree_hash: str | None = None
    pending_rebase_files: dict[str, str] | None = None
    pending_rebase_raw_files: dict[str, str] | None = None


def load_workspace_sync_state(workspace_root: Path | str, workspace: str) -> WorkspaceSyncState:
    state_path = _get_state_path(workspace_root, workspace)
    if not state_path.exists():
        return WorkspaceSyncState(workspace=workspace)

    data = json.loads(state_path.read_text(encoding="utf-8"))
    return WorkspaceSyncState(
        workspace=workspace,
        last_pulled_revision=data.get("last_pulled_revision"),
        last_pushed_revision=data.get("last_pushed_revision"),
        last_synced_tree_hash=data.get("last_synced_tree_hash"),
        last_sync_commit=data.get("last_sync_commit"),
        last_synced_files=_normalize_synced_files(data.get("last_synced_files")),
        last_synced_raw_files=_normalize_synced_files(data.get("last_synced_raw_files")),
        pending_rebase_revision=data.get("pending_rebase_revision"),
        pending_rebase_tree_hash=data.get("pending_rebase_tree_hash"),
        pending_rebase_files=_normalize_synced_files(data.get("pending_rebase_files")),
        pending_rebase_raw_files=_normalize_synced_files(data.get("pending_rebase_raw_files")),
    )


def save_workspace_sync_state(workspace_root: Path | str, state: WorkspaceSyncState) -> Path:
    state_path = _get_state_path(workspace_root, state.workspace)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(asdict(state), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state_path


def _get_state_path(workspace_root: Path | str, workspace: str) -> Path:
    return resolve_cache_root(workspace_root) / "state" / f"{workspace}.json"


def _normalize_synced_files(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    normalized: dict[str, str] = {}
    for key, item in value.items():
        if isinstance(key, str) and isinstance(item, str):
            normalized[key] = item
    return normalized
