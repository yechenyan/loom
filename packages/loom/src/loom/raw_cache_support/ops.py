from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import shutil

from .local_sources import find_local_scan_source_file
from .paths import resolve_raw_cache_dir


def get_cached_raw_path(workspace_root, workspace: str, relative_path: str) -> Path:
    return resolve_raw_cache_dir(workspace_root, workspace) / Path(relative_path)


def is_cached_raw_path_healthy(path: Path) -> bool:
    return (path.resolve(strict=False).exists() and path.exists()) if path.is_symlink() else path.is_file()


def is_cached_raw_path_current(path: Path, expected_sha256: str) -> bool:
    target_path = path.resolve() if path.is_symlink() else path
    return is_cached_raw_path_healthy(path) and sha256(target_path.read_bytes()).hexdigest() == expected_sha256


def populate_raw_cache_from_local_source(workspace_root, workspace: str, relative_path: str) -> Path | None:
    cache_path = get_cached_raw_path(workspace_root, workspace, relative_path)
    source_path = find_local_scan_source_file(workspace_root, workspace, relative_path)
    if source_path is not None:
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
