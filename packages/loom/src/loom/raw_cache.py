from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
from typing import Any


@dataclass
class RawCacheState:
    workspace: str
    manifest: dict[str, dict[str, str | int]] | None = None


def resolve_workspace_root(workspace_root: Path | str | None = None) -> Path:
    if workspace_root is not None:
        return Path(workspace_root).resolve()
    configured = os.environ.get("LOOM_WORKSPACE_ROOT")
    if configured:
        return Path(configured).resolve()
    return Path.cwd().resolve()


def resolve_loom_root(workspace_root: Path | str | None = None) -> Path:
    return resolve_workspace_root(workspace_root) / "test-project" / "loom"


def resolve_cache_root(workspace_root: Path | str | None = None) -> Path:
    return resolve_loom_root(workspace_root) / ".loom"


def resolve_raw_cache_dir(workspace_root: Path | str | None, workspace: str) -> Path:
    return resolve_cache_root(workspace_root) / "raw" / workspace


def load_raw_cache_state(workspace_root: Path | str | None, workspace: str) -> RawCacheState:
    state_path = _get_state_path(workspace_root, workspace)
    if not state_path.exists():
        return RawCacheState(workspace=workspace)

    data = json.loads(state_path.read_text(encoding="utf-8"))
    return RawCacheState(
        workspace=workspace,
        manifest=_normalize_manifest(data.get("manifest")),
    )


def save_raw_cache_state(workspace_root: Path | str | None, state: RawCacheState) -> Path:
    state_path = _get_state_path(workspace_root, state.workspace)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(asdict(state), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state_path


def get_cached_raw_path(workspace_root: Path | str | None, workspace: str, relative_path: str) -> Path:
    return resolve_raw_cache_dir(workspace_root, workspace) / Path(relative_path)


def is_cached_raw_path_healthy(path: Path) -> bool:
    if path.is_symlink():
        target = path.resolve(strict=False)
        return target.exists() and path.exists()
    return path.is_file()


def is_cached_raw_path_current(path: Path, expected_sha256: str) -> bool:
    if not is_cached_raw_path_healthy(path):
        return False
    target_path = path.resolve() if path.is_symlink() else path
    return _hash_file(target_path) == expected_sha256


def populate_raw_cache_from_local_source(
    workspace_root: Path | str | None,
    workspace: str,
    relative_path: str,
) -> Path | None:
    cache_path = get_cached_raw_path(workspace_root, workspace, relative_path)
    for raw_root in _iter_local_raw_roots(workspace_root):
        source_path = raw_root / workspace / relative_path
        if not source_path.is_file():
            continue
        _materialize_cache_path(cache_path, source_path)
        return cache_path
    return None


def write_raw_cache_file(
    workspace_root: Path | str | None,
    workspace: str,
    relative_path: str,
    content: bytes,
) -> Path:
    cache_path = get_cached_raw_path(workspace_root, workspace, relative_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(content)
    return cache_path


def remove_deleted_raw_cache_paths(
    workspace_root: Path | str | None,
    workspace: str,
    deleted_paths: list[str] | tuple[str, ...],
) -> None:
    workspace_dir = resolve_raw_cache_dir(workspace_root, workspace)
    for relative_path in deleted_paths:
        cache_path = workspace_dir / relative_path
        if cache_path.exists() or cache_path.is_symlink():
            cache_path.unlink()
            _cleanup_empty_parents(cache_path.parent, workspace_dir)


def _iter_local_raw_roots(workspace_root: Path | str | None) -> tuple[Path, ...]:
    root = resolve_workspace_root(workspace_root)
    candidates = [
        root / "test-project" / "loom" / "loom_raw",
        root / ".raw_data",
    ]
    configured = os.environ.get("LOOM_RAW_ROOT")
    if configured:
        candidates.insert(0, Path(configured).resolve())

    deduped: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(resolved)
    return tuple(deduped)


def _materialize_cache_path(cache_path: Path, source_path: Path) -> None:
    if cache_path.exists() or cache_path.is_symlink():
        cache_path.unlink()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        cache_path.symlink_to(source_path)
    except OSError:
        shutil.copy2(source_path, cache_path)


def _get_state_path(workspace_root: Path | str | None, workspace: str) -> Path:
    return resolve_cache_root(workspace_root) / "state" / f"raw-{workspace}.json"


def _normalize_manifest(value: Any) -> dict[str, dict[str, str | int]] | None:
    if not isinstance(value, dict):
        return None
    manifest: dict[str, dict[str, str | int]] = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, dict):
            continue
        sha256 = item.get("sha256")
        size_bytes = item.get("size_bytes")
        if isinstance(sha256, str) and isinstance(size_bytes, int):
            manifest[key] = {"sha256": sha256, "size_bytes": size_bytes}
    return manifest


def _cleanup_empty_parents(start_dir: Path, stop_dir: Path) -> None:
    current = start_dir
    while current != stop_dir and current.is_dir():
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def _hash_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()
