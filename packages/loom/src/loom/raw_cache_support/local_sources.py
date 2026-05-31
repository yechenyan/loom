from __future__ import annotations

from pathlib import Path

from ..scan_state import load_scan_state
from ..scan_support.state import normalize_scan_sources
from .paths import resolve_local_raw_workspace_dir, resolve_workspace_root


def iter_local_scan_source_roots(workspace_root, workspace: str) -> tuple[Path, ...]:
    root = resolve_workspace_root(workspace_root)
    state = load_scan_state(root, workspace)
    candidates = [
        _resolve_source_path(root, source["source_path"])
        for source in normalize_scan_sources(state).values()
    ]
    seen: set[Path] = set()
    deduped: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved not in seen:
            seen.add(resolved)
            deduped.append(resolved)
    return tuple(deduped)


def find_local_scan_source_file(workspace_root, workspace: str, relative_path: str) -> Path | None:
    for source_root in iter_local_scan_source_roots(workspace_root, workspace):
        for candidate_relative_path in _local_source_candidates(source_root, relative_path):
            candidate = source_root / candidate_relative_path
            if candidate.is_file():
                return candidate
    fallback = resolve_local_raw_workspace_dir(workspace_root, workspace) / relative_path
    if fallback.is_file():
        return fallback
    return None


def find_local_notice_dir(workspace_root, workspace: str) -> Path | None:
    for source_root in iter_local_scan_source_roots(workspace_root, workspace):
        loom_md_path = source_root / "loom.md"
        if loom_md_path.is_file():
            return source_root
    source_roots = iter_local_scan_source_roots(workspace_root, workspace)
    if source_roots:
        return source_roots[0]
    fallback = resolve_local_raw_workspace_dir(workspace_root, workspace)
    return fallback if fallback.exists() else None


def _resolve_source_path(workspace_root: Path, source_path: str) -> Path:
    source = Path(source_path).expanduser()
    return source if source.is_absolute() else workspace_root / source


def canonicalize_source_relative_path(source_root: Path, relative_path: str) -> str:
    if _source_root_is_dataset(source_root):
        return f"{source_root.name}/{relative_path}" if relative_path else source_root.name
    return relative_path


def _local_source_candidates(source_root: Path, relative_path: str) -> tuple[str, ...]:
    candidates = [relative_path]
    if _source_root_is_dataset(source_root):
        prefix = f"{source_root.name}/"
        if relative_path == source_root.name:
            candidates.append("")
        elif relative_path.startswith(prefix):
            candidates.append(relative_path[len(prefix) :])
    return tuple(dict.fromkeys(candidates))


def _source_root_is_dataset(source_root: Path) -> bool:
    return (source_root / "loom.md").is_file()
