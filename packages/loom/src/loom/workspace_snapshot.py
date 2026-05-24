from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import base64
import shutil

from .explore_repo import ensure_explore_repo, get_explore_repo_dir, list_workspaces


@dataclass(frozen=True)
class WorkspaceFileSnapshot:
    path: str
    sha256: str
    content: bytes


@dataclass(frozen=True)
class WorkspaceSnapshot:
    workspace: str
    files: tuple[WorkspaceFileSnapshot, ...]
    tree_hash: str


@dataclass(frozen=True)
class WorkspaceDelta:
    changed_files: tuple[WorkspaceFileSnapshot, ...]
    deleted_paths: tuple[str, ...]


def build_workspace_snapshot(workspace_root: Path | str, workspace: str) -> WorkspaceSnapshot:
    ensure_explore_repo(workspace_root)
    workspace_dir = get_explore_repo_dir(workspace_root) / workspace
    files: list[WorkspaceFileSnapshot] = []

    if workspace_dir.exists():
        for path in sorted(workspace_dir.rglob("*")):
            if not path.is_file():
                continue
            relative_path = path.relative_to(workspace_dir).as_posix()
            content = path.read_bytes()
            files.append(
                WorkspaceFileSnapshot(
                    path=relative_path,
                    sha256=sha256(content).hexdigest(),
                    content=content,
                )
            )

    return WorkspaceSnapshot(workspace=workspace, files=tuple(files), tree_hash=_compute_tree_hash(files))


def apply_workspace_snapshot(
    workspace_root: Path | str,
    workspace: str,
    files: tuple[WorkspaceFileSnapshot, ...],
) -> Path:
    repo_dir = ensure_explore_repo(workspace_root)
    workspace_dir = repo_dir / workspace

    if workspace_dir.exists():
        shutil.rmtree(workspace_dir)
    workspace_dir.mkdir(parents=True, exist_ok=True)

    for file_snapshot in files:
        target_path = workspace_dir / file_snapshot.path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(file_snapshot.content)

    return workspace_dir


def apply_workspace_delta(
    workspace_root: Path | str,
    workspace: str,
    changed_files: tuple[WorkspaceFileSnapshot, ...],
    deleted_paths: tuple[str, ...],
) -> Path:
    repo_dir = ensure_explore_repo(workspace_root)
    workspace_dir = repo_dir / workspace
    workspace_dir.mkdir(parents=True, exist_ok=True)

    for relative_path in deleted_paths:
        target_path = workspace_dir / relative_path
        if target_path.exists():
            target_path.unlink()
            _cleanup_empty_parents(target_path.parent, workspace_dir)

    for file_snapshot in changed_files:
        target_path = workspace_dir / file_snapshot.path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(file_snapshot.content)

    return workspace_dir


def encode_snapshot_files(snapshot: WorkspaceSnapshot) -> list[dict[str, str | int]]:
    return encode_workspace_files(snapshot.files)


def encode_workspace_files(files: tuple[WorkspaceFileSnapshot, ...] | list[WorkspaceFileSnapshot]) -> list[dict[str, str | int]]:
    payload: list[dict[str, str | int]] = []
    for file_snapshot in files:
        payload.append(
            {
                "path": file_snapshot.path,
                "sha256": file_snapshot.sha256,
                "content_base64": base64.b64encode(file_snapshot.content).decode("ascii"),
                "size_bytes": len(file_snapshot.content),
            }
        )
    return payload


def decode_snapshot_files(payload: list[dict[str, str | int]]) -> tuple[WorkspaceFileSnapshot, ...]:
    files: list[WorkspaceFileSnapshot] = []
    for item in payload:
        content = base64.b64decode(str(item["content_base64"]).encode("ascii"))
        files.append(
            WorkspaceFileSnapshot(
                path=str(item["path"]),
                sha256=str(item["sha256"]),
                content=content,
            )
        )
    return tuple(files)


def list_local_workspaces(workspace_root: Path | str) -> tuple[str, ...]:
    return list_workspaces(workspace_root)


def build_snapshot_manifest(snapshot: WorkspaceSnapshot) -> dict[str, str]:
    return {file_snapshot.path: file_snapshot.sha256 for file_snapshot in snapshot.files}


def build_workspace_delta(snapshot: WorkspaceSnapshot, previous_manifest: dict[str, str] | None) -> WorkspaceDelta:
    previous = previous_manifest or {}
    current_paths = {file_snapshot.path for file_snapshot in snapshot.files}
    changed_files = tuple(
        file_snapshot
        for file_snapshot in snapshot.files
        if previous.get(file_snapshot.path) != file_snapshot.sha256
    )
    deleted_paths = tuple(sorted(path for path in previous if path not in current_paths))
    return WorkspaceDelta(changed_files=changed_files, deleted_paths=deleted_paths)


def _compute_tree_hash(files: list[WorkspaceFileSnapshot]) -> str:
    digest = sha256()
    for file_snapshot in files:
        digest.update(file_snapshot.path.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_snapshot.sha256.encode("ascii"))
        digest.update(b"\0")
    return digest.hexdigest()


def _cleanup_empty_parents(start_dir: Path, stop_dir: Path) -> None:
    current = start_dir
    while current != stop_dir and current.is_dir():
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent
