from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import base64
import uuid

import sqlalchemy as sa

from .errors import WorkspaceConflictError, WorkspaceNotFoundError
from .helpers import blob_storage_path, compute_tree_hash, raw_blob_storage_path
from .queries import get_raw_current_manifest, get_revision_manifest, get_revision_tree_hash, get_workspace_row, raw_object_exists
from .raw_maps import apply_raw_mapping_updates
from .schema import metadata, raw_objects_table, workspace_revision_files_table, workspace_revisions_table, workspaces_table


class LoomSyncService:
    def __init__(self, database_url: str, storage_root: Path | str) -> None:
        self.database_url = database_url
        self.storage_root = Path(storage_root)
        self.engine = sa.create_engine(database_url, future=True)

    def init_db(self) -> None:
        self.storage_root.mkdir(parents=True, exist_ok=True)
        metadata.create_all(self.engine)

    def list_workspaces(self) -> list[dict[str, str | None]]:
        with self.engine.begin() as connection:
            rows = connection.execute(sa.select(workspaces_table.c.name, workspaces_table.c.head_revision_id).order_by(workspaces_table.c.name)).mappings()
            return [dict(row) for row in rows]

    def get_workspace_head(self, workspace: str) -> dict[str, str | None]:
        with self.engine.begin() as connection:
            workspace_row = get_workspace_row(connection, workspace)
            if workspace_row is None:
                raise WorkspaceNotFoundError(f"Remote workspace `{workspace}` was not found.")
            return {"workspace": workspace, "head_revision_id": workspace_row["head_revision_id"]}

    def get_missing_raw_hashes(self, hashes: list[str]) -> list[str]:
        normalized_hashes = sorted({item for item in hashes if item})
        with self.engine.begin() as connection:
            rows = connection.execute(sa.select(raw_objects_table.c.sha256).where(raw_objects_table.c.sha256.in_(normalized_hashes))).scalars()
            existing = {str(value) for value in rows}
        return [value for value in normalized_hashes if value not in existing]

    def get_workspace_raw_manifest(self, workspace: str) -> dict[str, dict[str, str | int]]:
        with self.engine.begin() as connection:
            workspace_row = get_workspace_row(connection, workspace)
            if workspace_row is None:
                raise WorkspaceNotFoundError(f"Remote workspace `{workspace}` was not found.")
            raw_manifest = get_raw_current_manifest(connection, int(workspace_row["id"]))
        return {path: {"sha256": str(item["sha256"]), "size_bytes": int(item["size_bytes"])} for path, item in sorted(raw_manifest.items())}

    def get_raw_object(self, file_sha256: str) -> dict[str, str | int]:
        with self.engine.begin() as connection:
            row = connection.execute(sa.select(raw_objects_table).where(raw_objects_table.c.sha256 == file_sha256)).mappings().first()
            if row is None:
                raise WorkspaceNotFoundError(f"Raw object `{file_sha256}` was not found.")
            content = (self.storage_root / str(row["storage_path"])).read_bytes()
        return {"sha256": file_sha256, "size_bytes": int(row["size_bytes"]), "content_base64": base64.b64encode(content).decode("ascii")}

    def store_raw_objects(self, objects: list[dict[str, str | int]]) -> int:
        stored_count = 0
        with self.engine.begin() as connection:
            for item in objects:
                if raw_object_exists(connection, str(item["sha256"])) is not None:
                    continue
                stored_count += _store_raw_object(connection, self.storage_root, item)
        return stored_count

    def push_workspace(self, workspace: str, *, base_revision: str | None, local_commit: str | None, tree_hash: str, message: str, files, deleted_paths, raw_files, raw_deleted_paths):
        return _push_workspace(self.engine, self.storage_root, workspace, base_revision, local_commit, tree_hash, message, files, deleted_paths, raw_files, raw_deleted_paths)

    def pull_workspace(self, workspace: str, *, base_revision: str | None = None):
        return _pull_workspace(self.engine, self.storage_root, workspace, base_revision)


def _store_raw_object(connection: sa.Connection, storage_root: Path, item) -> int:
    file_sha256 = str(item["sha256"])
    content = base64.b64decode(str(item["content_base64"]).encode("ascii"))
    if sha256(content).hexdigest() != file_sha256:
        raise ValueError(f"Raw object sha256 mismatch: expected {file_sha256}.")
    storage_path = raw_blob_storage_path(storage_root, file_sha256)
    if not storage_path.exists():
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_bytes(content)
    connection.execute(raw_objects_table.insert().values(sha256=file_sha256, size_bytes=int(item["size_bytes"]), storage_path=str(storage_path.relative_to(storage_root)), created_at=datetime.now(timezone.utc)))
    return 1


def _push_workspace(engine, storage_root, workspace, base_revision, local_commit, tree_hash, message, files, deleted_paths, raw_files, raw_deleted_paths):
    timestamp = datetime.now(timezone.utc)
    with engine.begin() as connection:
        workspace_row = get_workspace_row(connection, workspace) or _create_workspace(connection, workspace, timestamp)
        current_head = workspace_row["head_revision_id"]
        if current_head is not None and base_revision != current_head:
            raise WorkspaceConflictError(f"Remote workspace `{workspace}` has advanced to revision `{current_head}`.")
        base_manifest = get_revision_manifest(connection, base_revision) if base_revision else {}
        next_manifest = _next_manifest(storage_root, base_manifest, files, deleted_paths)
        raw_current_manifest = get_raw_current_manifest(connection, int(workspace_row["id"]))
        next_tree_hash = compute_tree_hash(next_manifest)
        if next_tree_hash != tree_hash:
            raise ValueError(f"Tree hash mismatch: expected {tree_hash}, got {next_tree_hash}.")
        revision_id = current_head if current_head and next_tree_hash == get_revision_tree_hash(connection, current_head) else _insert_revision(connection, workspace_row["id"], current_head, tree_hash, message, local_commit, next_manifest, timestamp)
        apply_raw_mapping_updates(connection, workspace_id=int(workspace_row["id"]), revision_id=revision_id, raw_files=raw_files, raw_deleted_paths=raw_deleted_paths, current_manifest=raw_current_manifest, timestamp=timestamp)
        connection.execute(workspaces_table.update().where(workspaces_table.c.id == workspace_row["id"]).values(head_revision_id=revision_id, updated_at=timestamp))
    return {"workspace": workspace, "revision_id": revision_id, "parent_revision_id": current_head, "tree_hash": next_tree_hash, "file_count": len(next_manifest), "changed_file_count": len(files), "deleted_file_count": len(deleted_paths), "raw_mapping_changed_count": len(raw_files), "raw_mapping_deleted_count": len(raw_deleted_paths), "raw_current_file_count": len(raw_current_manifest) + len(raw_files) - len(raw_deleted_paths)}


def _pull_workspace(engine, storage_root, workspace, base_revision):
    with engine.begin() as connection:
        workspace_row = get_workspace_row(connection, workspace)
        if workspace_row is None or workspace_row["head_revision_id"] is None:
            raise WorkspaceNotFoundError(f"Remote workspace `{workspace}` was not found.")
        revision_row = connection.execute(sa.select(workspace_revisions_table).where(workspace_revisions_table.c.revision_id == workspace_row["head_revision_id"])).mappings().one()
        head_manifest = get_revision_manifest(connection, workspace_row["head_revision_id"])
        base_manifest = get_revision_manifest(connection, base_revision) if base_revision else {}
        files_payload = [_encode_file_payload(storage_root, path, file_entry) for path, file_entry in sorted(head_manifest.items()) if base_manifest.get(path, {}).get("sha256") != file_entry["sha256"]]
        deleted_paths = sorted(path for path in base_manifest if path not in head_manifest)
        raw_manifest = get_raw_current_manifest(connection, int(workspace_row["id"]))
    return {"workspace": workspace, "revision_id": str(revision_row["revision_id"]), "parent_revision_id": revision_row["parent_revision_id"], "tree_hash": str(revision_row["tree_hash"]), "message": str(revision_row["message"]), "local_commit": revision_row["local_commit"], "file_count": int(revision_row["file_count"]), "changed_file_count": len(files_payload), "deleted_file_count": len(deleted_paths), "deleted_paths": deleted_paths, "raw_manifest": {path: {"sha256": str(entry["sha256"]), "size_bytes": int(entry["size_bytes"])} for path, entry in sorted(raw_manifest.items())}, "files": files_payload}


def _create_workspace(connection, workspace: str, timestamp):
    connection.execute(workspaces_table.insert().values(name=workspace, head_revision_id=None, created_at=timestamp, updated_at=timestamp))
    row = get_workspace_row(connection, workspace)
    assert row is not None
    return row


def _next_manifest(storage_root: Path, base_manifest, files, deleted_paths):
    manifest = dict(base_manifest)
    for path in deleted_paths:
        manifest.pop(path, None)
    for item in files:
        content = base64.b64decode(str(item["content_base64"]).encode("ascii"))
        file_sha256 = str(item["sha256"])
        if sha256(content).hexdigest() != file_sha256:
            raise ValueError(f"File payload sha256 mismatch for `{item['path']}`.")
        storage_path = blob_storage_path(storage_root, file_sha256)
        if not storage_path.exists():
            storage_path.parent.mkdir(parents=True, exist_ok=True)
            storage_path.write_bytes(content)
        manifest[str(item["path"])] = {"path": str(item["path"]), "sha256": file_sha256, "size_bytes": int(item["size_bytes"]), "storage_path": str(storage_path.relative_to(storage_root))}
    return manifest


def _insert_revision(connection, workspace_id, current_head, tree_hash, message, local_commit, next_manifest, timestamp):
    revision_id = uuid.uuid4().hex
    connection.execute(workspace_revisions_table.insert().values(workspace_id=workspace_id, revision_id=revision_id, parent_revision_id=current_head, tree_hash=tree_hash, message=message, local_commit=local_commit, file_count=len(next_manifest), created_at=timestamp))
    for file_entry in next_manifest.values():
        connection.execute(workspace_revision_files_table.insert().values(revision_id=revision_id, path=str(file_entry["path"]), sha256=str(file_entry["sha256"]), size_bytes=int(file_entry["size_bytes"]), storage_path=str(file_entry["storage_path"])))
    return revision_id


def _encode_file_payload(storage_root: Path, path: str, file_entry):
    content = (storage_root / str(file_entry["storage_path"])).read_bytes()
    return {"path": path, "sha256": str(file_entry["sha256"]), "size_bytes": int(file_entry["size_bytes"]), "content_base64": base64.b64encode(content).decode("ascii")}
