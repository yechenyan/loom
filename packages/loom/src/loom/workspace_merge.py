from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile

from .workspace_snapshot import WorkspaceFileSnapshot, WorkspaceSnapshot


@dataclass(frozen=True)
class WorkspaceMergeResult:
    files: tuple[WorkspaceFileSnapshot, ...]
    deleted_paths: tuple[str, ...]
    conflict_paths: tuple[str, ...]


def merge_workspace_snapshots(
    *,
    workspace: str,
    base: WorkspaceSnapshot,
    local: WorkspaceSnapshot,
    remote: WorkspaceSnapshot,
) -> WorkspaceMergeResult:
    base_map = {item.path: item for item in base.files}
    local_map = {item.path: item for item in local.files}
    remote_map = {item.path: item for item in remote.files}

    merged_files: list[WorkspaceFileSnapshot] = []
    deleted_paths: list[str] = []
    conflict_paths: list[str] = []

    for path in sorted(set(base_map) | set(local_map) | set(remote_map)):
        merged_content, conflict = _merge_path(
            path=path,
            base=base_map.get(path),
            local=local_map.get(path),
            remote=remote_map.get(path),
        )
        if merged_content is None:
            deleted_paths.append(path)
            continue
        merged_files.append(WorkspaceFileSnapshot(path=path, sha256=_hash_bytes(merged_content), content=merged_content))
        if conflict:
            conflict_paths.append(path)

    return WorkspaceMergeResult(
        files=tuple(merged_files),
        deleted_paths=tuple(deleted_paths),
        conflict_paths=tuple(conflict_paths),
    )


def _merge_path(
    *,
    path: str,
    base: WorkspaceFileSnapshot | None,
    local: WorkspaceFileSnapshot | None,
    remote: WorkspaceFileSnapshot | None,
) -> tuple[bytes | None, bool]:
    base_content = base.content if base is not None else None
    local_content = local.content if local is not None else None
    remote_content = remote.content if remote is not None else None

    if local_content == remote_content:
        return local_content, False
    if local_content == base_content:
        return remote_content, False
    if remote_content == base_content:
        return local_content, False

    if base_content is None:
        if local_content is None:
            return remote_content, False
        if remote_content is None:
            return local_content, False
        return _render_conflict(path, local_content, remote_content, base_content, "added"), True

    if local_content is None:
        if remote_content is None:
            return None, False
        return _render_conflict(path, b"", remote_content, base_content, "deleted-locally"), True

    if remote_content is None:
        return _render_conflict(path, local_content, b"", base_content, "deleted-remotely"), True

    if _looks_binary(base_content) or _looks_binary(local_content) or _looks_binary(remote_content):
        return _render_conflict(path, local_content, remote_content, base_content, "binary"), True

    merged_text, conflict = _merge_text(local_content, base_content, remote_content, path)
    return merged_text, conflict


def _merge_text(local_content: bytes, base_content: bytes, remote_content: bytes, path: str) -> tuple[bytes, bool]:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        current_path = temp_root / "current.txt"
        base_path = temp_root / "base.txt"
        other_path = temp_root / "other.txt"
        current_path.write_bytes(local_content)
        base_path.write_bytes(base_content)
        other_path.write_bytes(remote_content)

        result = subprocess.run(
            [
                "git",
                "merge-file",
                "-p",
                "-L",
                f"LOCAL:{path}",
                "-L",
                f"BASE:{path}",
                "-L",
                f"REMOTE:{path}",
                str(current_path),
                str(base_path),
                str(other_path),
            ],
            check=False,
            capture_output=True,
        )
        if result.returncode not in (0, 1):
            raise RuntimeError(result.stderr.decode("utf-8", errors="replace").strip() or "git merge-file failed")
        return result.stdout, result.returncode == 1


def _render_conflict(
    path: str,
    local_content: bytes | None,
    remote_content: bytes | None,
    base_content: bytes | None,
    reason: str,
) -> bytes:
    local_text = _safe_decode(local_content)
    remote_text = _safe_decode(remote_content)
    base_text = _safe_decode(base_content)
    return (
        f"<<<<<<< LOCAL:{path}\n"
        f"{local_text}"
        f"||||||| BASE:{path}\n"
        f"{base_text}"
        f"=======\n"
        f"{remote_text}"
        f">>>>>>> REMOTE:{path}\n"
        f"\n[loom conflict reason: {reason}]\n"
    ).encode("utf-8")


def _safe_decode(content: bytes | None) -> str:
    if content is None:
        return ""
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        return "[binary content omitted]\n"
    if text and not text.endswith("\n"):
        text += "\n"
    return text


def _hash_bytes(content: bytes) -> str:
    import hashlib

    return hashlib.sha256(content).hexdigest()


def _looks_binary(content: bytes | None) -> bool:
    return content is not None and b"\0" in content
