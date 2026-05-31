from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path

from .raw_cache_support.local_sources import iter_local_scan_source_roots
from .scan_state import hash_file


@dataclass(frozen=True)
class RawFileSnapshot:
    path: str
    sha256: str
    size_bytes: int
    content: bytes


@dataclass(frozen=True)
class RawWorkspaceSnapshot:
    workspace: str
    files: tuple[RawFileSnapshot, ...]


@dataclass(frozen=True)
class RawWorkspaceDelta:
    changed_files: tuple[RawFileSnapshot, ...]
    deleted_paths: tuple[str, ...]


def build_raw_workspace_snapshot(workspace_root: Path | str, workspace: str) -> RawWorkspaceSnapshot:
    files: list[RawFileSnapshot] = []
    seen_paths: set[str] = set()

    for source_root in iter_local_scan_source_roots(Path(workspace_root), workspace):
        if not source_root.exists():
            continue
        for path in sorted(source_root.rglob("*")):
            if not path.is_file():
                continue
            relative_path = path.relative_to(source_root).as_posix()
            if relative_path in seen_paths:
                continue
            seen_paths.add(relative_path)
            files.append(
                RawFileSnapshot(
                    path=relative_path,
                    sha256=hash_file(path),
                    size_bytes=path.stat().st_size,
                    content=path.read_bytes(),
                )
            )

    return RawWorkspaceSnapshot(workspace=workspace, files=tuple(files))


def build_raw_manifest(snapshot: RawWorkspaceSnapshot) -> dict[str, str]:
    return {file_snapshot.path: file_snapshot.sha256 for file_snapshot in snapshot.files}


def build_raw_workspace_delta(
    snapshot: RawWorkspaceSnapshot, previous_manifest: dict[str, str] | None
) -> RawWorkspaceDelta:
    previous = previous_manifest or {}
    current_paths = {file_snapshot.path for file_snapshot in snapshot.files}
    changed_files = tuple(
        file_snapshot
        for file_snapshot in snapshot.files
        if previous.get(file_snapshot.path) != file_snapshot.sha256
    )
    deleted_paths = tuple(sorted(path for path in previous if path not in current_paths))
    return RawWorkspaceDelta(changed_files=changed_files, deleted_paths=deleted_paths)


def encode_raw_files(files: tuple[RawFileSnapshot, ...] | list[RawFileSnapshot]) -> list[dict[str, str | int]]:
    payload: list[dict[str, str | int]] = []
    for file_snapshot in files:
        payload.append(
            {
                "path": file_snapshot.path,
                "sha256": file_snapshot.sha256,
                "size_bytes": file_snapshot.size_bytes,
                "content_base64": base64.b64encode(file_snapshot.content).decode("ascii"),
            }
        )
    return payload
