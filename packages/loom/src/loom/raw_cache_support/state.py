from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from typing import Any

from .paths import resolve_cache_root


@dataclass
class RawCacheState:
    workspace: str
    manifest: dict[str, dict[str, str | int]] | None = None


def load_raw_cache_state(workspace_root, workspace: str) -> RawCacheState:
    state_path = resolve_cache_root(workspace_root) / "state" / f"raw-{workspace}.json"
    if not state_path.exists():
        return RawCacheState(workspace=workspace)
    data = json.loads(state_path.read_text(encoding="utf-8"))
    return RawCacheState(workspace=workspace, manifest=_normalize_manifest(data.get("manifest")))


def save_raw_cache_state(workspace_root, state: RawCacheState):
    state_path = resolve_cache_root(workspace_root) / "state" / f"raw-{state.workspace}.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(asdict(state), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state_path


def _normalize_manifest(value: Any) -> dict[str, dict[str, str | int]] | None:
    if not isinstance(value, dict):
        return None
    manifest: dict[str, dict[str, str | int]] = {}
    for key, item in value.items():
        if isinstance(key, str) and isinstance(item, dict) and isinstance(item.get("sha256"), str) and isinstance(item.get("size_bytes"), int):
            manifest[key] = {"sha256": item["sha256"], "size_bytes": item["size_bytes"]}
    return manifest
