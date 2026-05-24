from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import shutil

from .paths import resolve_loom_root, resolve_raw_cache_dir, resolve_workspace_root


def get_cached_raw_path(workspace_root, workspace: str, relative_path: str) -> Path:
    return resolve_raw_cache_dir(workspace_root, workspace) / Path(relative_path)


def is_cached_raw_path_healthy(path: Path) -> bool:
    return (path.resolve(strict=False).exists() and path.exists()) if path.is_symlink() else path.is_file()


def is_cached_raw_path_current(path: Path, expected_sha256: str) -> bool:
    target_path = path.resolve() if path.is_symlink() else path
    return is_cached_raw_path_healthy(path) and sha256(target_path.read_bytes()).hexdigest() == expected_sha256


def populate_raw_cache_from_local_source(workspace_root, workspace: str, relative_path: str) -> Path | None:
    cache_path = get_cached_raw_path(workspace_root, workspace, relative_path)
    for raw_root in _iter_local_raw_roots(workspace_root):
        source_path = raw_root / workspace / relative_path
        if source_path.is_file():
            _materialize_cache_path(cache_path, source_path)
            return cache_path
    return None


def write_raw_cache_file(workspace_root, workspace: str, relative_path: str, content: bytes) -> Path:
    cache_path = get_cached_raw_path(workspace_root, workspace, relative_path)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_bytes(content)
    return cache_path


def list_cached_raw_paths(workspace_root, workspace: str) -> tuple[str, ...]:
    workspace_dir = resolve_raw_cache_dir(workspace_root, workspace)
    if not workspace_dir.exists():
        return ()
    return tuple(path.relative_to(workspace_dir).as_posix() for path in sorted(workspace_dir.rglob("*")) if path.is_file() or path.is_symlink())


def remove_deleted_raw_cache_paths(workspace_root, workspace: str, deleted_paths: list[str] | tuple[str, ...]) -> None:
    workspace_dir = resolve_raw_cache_dir(workspace_root, workspace)
    for relative_path in deleted_paths:
        cache_path = workspace_dir / relative_path
        if cache_path.exists() or cache_path.is_symlink():
            cache_path.unlink()
            _cleanup_empty_parents(cache_path.parent, workspace_dir)


def _iter_local_raw_roots(workspace_root) -> tuple[Path, ...]:
    root = resolve_workspace_root(workspace_root)
    candidates = [resolve_loom_root(root) / "loom_raw", root / ".raw_data"]
    if os.environ.get("LOOM_RAW_ROOT"):
        candidates.insert(0, Path(os.environ["LOOM_RAW_ROOT"]).resolve())
    seen: set[Path] = set()
    deduped: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
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


def _cleanup_empty_parents(start_dir: Path, stop_dir: Path) -> None:
    current = start_dir
    while current != stop_dir and current.is_dir():
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent
