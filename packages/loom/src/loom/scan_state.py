from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .raw_cache_support.paths import resolve_cache_root


def load_scan_state(workspace_root: Path | str, topic: str) -> dict[str, Any]:
    state_path = get_scan_state_path(workspace_root, topic)
    if not state_path.exists():
        return {"topic": topic, "datasets": {}}

    data = json.loads(state_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return {"topic": topic, "datasets": {}}
    data.setdefault("topic", topic)
    data.setdefault("datasets", {})
    return data


def save_scan_state(workspace_root: Path | str, topic: str, state: dict[str, Any]) -> Path:
    state_path = get_scan_state_path(workspace_root, topic)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return state_path


def get_scan_state_path(workspace_root: Path | str, topic: str) -> Path:
    return resolve_cache_root(workspace_root) / "state" / f"{topic}-scan.json"


def load_recent_workspace(workspace_root: Path | str) -> str | None:
    state_path = get_recent_workspace_state_path(workspace_root)
    if not state_path.exists():
        return None

    data = json.loads(state_path.read_text(encoding="utf-8"))
    workspace = data.get("workspace") if isinstance(data, dict) else None
    if not isinstance(workspace, str):
        return None
    normalized = workspace.strip().strip("/")
    return normalized or None


def save_recent_workspace(workspace_root: Path | str, workspace: str) -> Path:
    state_path = get_recent_workspace_state_path(workspace_root)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"workspace": workspace}
    state_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return state_path


def get_recent_workspace_state_path(workspace_root: Path | str) -> Path:
    return resolve_cache_root(workspace_root) / "state" / "recent-workspace.json"


def hash_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def hash_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()
