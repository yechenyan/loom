from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkspacePushResult:
    workspace: str
    revision_id: str | None
    tree_hash: str | None
    changed_file_count: int
    deleted_file_count: int
    raw_uploaded_object_count: int
    raw_mapping_changed_count: int
    raw_mapping_deleted_count: int
    conflicted: bool = False
    conflict_paths: tuple[str, ...] = ()
    raw_conflict_notice_path: str | None = None


@dataclass(frozen=True)
class WorkspacePullResult:
    workspace: str
    revision_id: str
    changed: bool
    changed_file_count: int
    deleted_file_count: int
    conflicted: bool = False
    conflict_paths: tuple[str, ...] = ()
    raw_conflict_notice_path: str | None = None


@dataclass(frozen=True)
class RawWorkspacePullResult:
    workspace: str
    downloaded_file_count: int
    linked_file_count: int
    deleted_file_count: int
    manifest_file_count: int
    raw_conflict_notice_path: str | None = None
