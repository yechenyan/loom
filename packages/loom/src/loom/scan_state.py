from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .raw_cache import resolve_cache_root


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


def hash_text(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def hash_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()
