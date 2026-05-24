from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import base64
import uuid

import sqlalchemy as sa


metadata = sa.MetaData()

workspaces_table = sa.Table(
    "loom_workspaces",
    metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("name", sa.String(length=255), nullable=False, unique=True),
    sa.Column("head_revision_id", sa.String(length=64), nullable=True),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
)

workspace_revisions_table = sa.Table(
    "loom_workspace_revisions",
    metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("loom_workspaces.id"), nullable=False),
    sa.Column("revision_id", sa.String(length=64), nullable=False, unique=True),
    sa.Column("parent_revision_id", sa.String(length=64), nullable=True),
    sa.Column("tree_hash", sa.String(length=64), nullable=False),
    sa.Column("message", sa.Text(), nullable=False),
    sa.Column("local_commit", sa.String(length=64), nullable=True),
    sa.Column("file_count", sa.Integer(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
)

workspace_revision_files_table = sa.Table(
    "loom_workspace_revision_files",
    metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("revision_id", sa.String(length=64), nullable=False),
    sa.Column("path", sa.Text(), nullable=False),
    sa.Column("sha256", sa.String(length=64), nullable=False),
    sa.Column("size_bytes", sa.Integer(), nullable=False),
    sa.Column("storage_path", sa.Text(), nullable=False),
)

raw_objects_table = sa.Table(
    "loom_raw_objects",
    metadata,
    sa.Column("sha256", sa.String(length=64), primary_key=True),
    sa.Column("size_bytes", sa.Integer(), nullable=False),
    sa.Column("storage_path", sa.Text(), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
)

workspace_raw_current_table = sa.Table(
    "loom_workspace_raw_current",
    metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("loom_workspaces.id"), nullable=False),
    sa.Column("path", sa.Text(), nullable=False),
    sa.Column("sha256", sa.String(length=64), nullable=False),
    sa.Column("size_bytes", sa.Integer(), nullable=False),
    sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    sa.UniqueConstraint("workspace_id", "path", name="uq_workspace_raw_current_path"),
)

workspace_raw_history_table = sa.Table(
    "loom_workspace_raw_history",
    metadata,
    sa.Column("id", sa.Integer(), primary_key=True),
    sa.Column("workspace_id", sa.Integer(), sa.ForeignKey("loom_workspaces.id"), nullable=False),
    sa.Column("revision_id", sa.String(length=64), nullable=True),
    sa.Column("path", sa.Text(), nullable=False),
    sa.Column("sha256", sa.String(length=64), nullable=True),
    sa.Column("size_bytes", sa.Integer(), nullable=True),
    sa.Column("action", sa.String(length=16), nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
)


class WorkspaceNotFoundError(RuntimeError):
    pass


class WorkspaceConflictError(RuntimeError):
    pass


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
            rows = connection.execute(
                sa.select(workspaces_table.c.name, workspaces_table.c.head_revision_id).order_by(workspaces_table.c.name)
            ).mappings()
            return [dict(row) for row in rows]

    def push_workspace(
        self,
        workspace: str,
        *,
        base_revision: str | None,
        local_commit: str | None,
        tree_hash: str,
        message: str,
        files: list[dict[str, str | int]],
        deleted_paths: list[str],
        raw_files: list[dict[str, str | int]],
        raw_deleted_paths: list[str],
    ) -> dict[str, str | int | None]:
        timestamp = datetime.now(timezone.utc)

        with self.engine.begin() as connection:
            workspace_row = self._get_workspace_row(connection, workspace)
            if workspace_row is None:
                connection.execute(
                    workspaces_table.insert().values(
                        name=workspace,
                        head_revision_id=None,
                        created_at=timestamp,
                        updated_at=timestamp,
                    )
                )
                workspace_row = self._get_workspace_row(connection, workspace)

            assert workspace_row is not None
            current_head = workspace_row["head_revision_id"]
            if current_head is not None and base_revision != current_head:
                raise WorkspaceConflictError(
                    f"Remote workspace `{workspace}` has advanced to revision `{current_head}`; "
                    f"cannot push incremental changes from base `{base_revision or '-'}`."
                )

            base_manifest = self._get_revision_manifest(connection, base_revision) if base_revision else {}
            next_manifest = dict(base_manifest)
            raw_current_manifest = self._get_raw_current_manifest(connection, int(workspace_row["id"]))

            for path in deleted_paths:
                next_manifest.pop(path, None)

            for file_payload in files:
                path = str(file_payload["path"])
                content = base64.b64decode(str(file_payload["content_base64"]).encode("ascii"))
                file_sha256 = str(file_payload["sha256"])
                actual_sha256 = sha256(content).hexdigest()
                if actual_sha256 != file_sha256:
                    raise ValueError(
                        f"File payload sha256 mismatch for `{path}`: expected {file_sha256}, got {actual_sha256}."
                    )

                storage_path = self._get_blob_storage_path(file_sha256)
                if not storage_path.exists():
                    storage_path.parent.mkdir(parents=True, exist_ok=True)
                    storage_path.write_bytes(content)

                next_manifest[path] = {
                    "path": path,
                    "sha256": file_sha256,
                    "size_bytes": int(file_payload["size_bytes"]),
                    "storage_path": str(storage_path.relative_to(self.storage_root)),
                }

            next_tree_hash = self._compute_tree_hash(next_manifest)
            if next_tree_hash != tree_hash:
                raise ValueError(f"Tree hash mismatch: expected {tree_hash}, got {next_tree_hash}.")

            if current_head is not None and next_tree_hash == self._get_revision_tree_hash(connection, current_head):
                self._apply_raw_mapping_updates(
                    connection,
                    workspace_id=int(workspace_row["id"]),
                    revision_id=current_head,
                    raw_files=raw_files,
                    raw_deleted_paths=raw_deleted_paths,
                    current_manifest=raw_current_manifest,
                    timestamp=timestamp,
                )
                return {
                    "workspace": workspace,
                    "revision_id": current_head,
                    "parent_revision_id": current_head,
                    "tree_hash": next_tree_hash,
                    "file_count": len(next_manifest),
                    "changed_file_count": len(files),
                    "deleted_file_count": len(deleted_paths),
                    "raw_mapping_changed_count": len(raw_files),
                    "raw_mapping_deleted_count": len(raw_deleted_paths),
                }

            revision_id = uuid.uuid4().hex
            connection.execute(
                workspace_revisions_table.insert().values(
                    workspace_id=workspace_row["id"],
                    revision_id=revision_id,
                    parent_revision_id=current_head,
                    tree_hash=tree_hash,
                    message=message,
                    local_commit=local_commit,
                    file_count=len(next_manifest),
                    created_at=timestamp,
                )
            )

            for file_entry in next_manifest.values():
                connection.execute(
                    workspace_revision_files_table.insert().values(
                        revision_id=revision_id,
                        path=str(file_entry["path"]),
                        sha256=str(file_entry["sha256"]),
                        size_bytes=int(file_entry["size_bytes"]),
                        storage_path=str(file_entry["storage_path"]),
                    )
                )

            self._apply_raw_mapping_updates(
                connection,
                workspace_id=int(workspace_row["id"]),
                revision_id=revision_id,
                raw_files=raw_files,
                raw_deleted_paths=raw_deleted_paths,
                current_manifest=raw_current_manifest,
                timestamp=timestamp,
            )

            connection.execute(
                workspaces_table.update()
                .where(workspaces_table.c.id == workspace_row["id"])
                .values(head_revision_id=revision_id, updated_at=timestamp)
            )

        return {
            "workspace": workspace,
            "revision_id": revision_id,
            "parent_revision_id": current_head,
            "tree_hash": next_tree_hash,
            "file_count": len(next_manifest),
            "changed_file_count": len(files),
            "deleted_file_count": len(deleted_paths),
            "raw_mapping_changed_count": len(raw_files),
            "raw_mapping_deleted_count": len(raw_deleted_paths),
            "raw_current_file_count": len(raw_current_manifest) + len(raw_files) - len(raw_deleted_paths),
        }

    def pull_workspace(
        self, workspace: str, *, base_revision: str | None = None
    ) -> dict[str, str | int | list[dict[str, str | int]]]:
        with self.engine.begin() as connection:
            workspace_row = self._get_workspace_row(connection, workspace)
            if workspace_row is None or workspace_row["head_revision_id"] is None:
                raise WorkspaceNotFoundError(f"Remote workspace `{workspace}` was not found.")

            revision_row = connection.execute(
                sa.select(workspace_revisions_table)
                .where(workspace_revisions_table.c.revision_id == workspace_row["head_revision_id"])
            ).mappings().one()

            file_rows = connection.execute(
                sa.select(workspace_revision_files_table)
                .where(workspace_revision_files_table.c.revision_id == workspace_row["head_revision_id"])
                .order_by(workspace_revision_files_table.c.path)
            ).mappings()

            head_manifest = {
                str(file_row["path"]): {
                    "path": str(file_row["path"]),
                    "sha256": str(file_row["sha256"]),
                    "size_bytes": int(file_row["size_bytes"]),
                    "storage_path": str(file_row["storage_path"]),
                }
                for file_row in file_rows
            }
            base_manifest = self._get_revision_manifest(connection, base_revision) if base_revision else {}
            files_payload: list[dict[str, str | int]] = []
            for path, file_entry in sorted(head_manifest.items()):
                base_entry = base_manifest.get(path)
                if base_entry is not None and str(base_entry["sha256"]) == str(file_entry["sha256"]):
                    continue
                stored_path = self.storage_root / str(file_entry["storage_path"])
                content = stored_path.read_bytes()
                files_payload.append(
                    {
                        "path": path,
                        "sha256": str(file_entry["sha256"]),
                        "size_bytes": int(file_entry["size_bytes"]),
                        "content_base64": base64.b64encode(content).decode("ascii"),
                    }
                )
            deleted_paths = sorted(path for path in base_manifest if path not in head_manifest)
            raw_manifest = self._get_raw_current_manifest(connection, int(workspace_row["id"]))

        return {
            "workspace": workspace,
            "revision_id": str(revision_row["revision_id"]),
            "parent_revision_id": revision_row["parent_revision_id"],
            "tree_hash": str(revision_row["tree_hash"]),
            "message": str(revision_row["message"]),
            "local_commit": revision_row["local_commit"],
            "file_count": int(revision_row["file_count"]),
            "changed_file_count": len(files_payload),
            "deleted_file_count": len(deleted_paths),
            "deleted_paths": deleted_paths,
            "raw_manifest": {
                path: {
                    "sha256": str(entry["sha256"]),
                    "size_bytes": int(entry["size_bytes"]),
                }
                for path, entry in sorted(raw_manifest.items())
            },
            "files": files_payload,
        }

    def get_workspace_head(self, workspace: str) -> dict[str, str | None]:
        with self.engine.begin() as connection:
            workspace_row = self._get_workspace_row(connection, workspace)
            if workspace_row is None:
                raise WorkspaceNotFoundError(f"Remote workspace `{workspace}` was not found.")
            return {
                "workspace": workspace,
                "head_revision_id": workspace_row["head_revision_id"],
            }

    def get_missing_raw_hashes(self, hashes: list[str]) -> list[str]:
        normalized_hashes = sorted({item for item in hashes if item})
        if not normalized_hashes:
            return []
        with self.engine.begin() as connection:
            rows = connection.execute(
                sa.select(raw_objects_table.c.sha256).where(raw_objects_table.c.sha256.in_(normalized_hashes))
            ).scalars()
            existing = {str(value) for value in rows}
        return [value for value in normalized_hashes if value not in existing]

    def get_workspace_raw_manifest(self, workspace: str) -> dict[str, dict[str, str | int]]:
        with self.engine.begin() as connection:
            workspace_row = self._get_workspace_row(connection, workspace)
            if workspace_row is None:
                raise WorkspaceNotFoundError(f"Remote workspace `{workspace}` was not found.")
            raw_manifest = self._get_raw_current_manifest(connection, int(workspace_row["id"]))
        return {
            path: {
                "sha256": str(item["sha256"]),
                "size_bytes": int(item["size_bytes"]),
            }
            for path, item in sorted(raw_manifest.items())
        }

    def get_raw_object(self, file_sha256: str) -> dict[str, str | int]:
        with self.engine.begin() as connection:
            row = connection.execute(
                sa.select(raw_objects_table).where(raw_objects_table.c.sha256 == file_sha256)
            ).mappings().first()
            if row is None:
                raise WorkspaceNotFoundError(f"Raw object `{file_sha256}` was not found.")
            storage_path = self.storage_root / str(row["storage_path"])
            content = storage_path.read_bytes()
        return {
            "sha256": file_sha256,
            "size_bytes": int(row["size_bytes"]),
            "content_base64": base64.b64encode(content).decode("ascii"),
        }

    def store_raw_objects(self, objects: list[dict[str, str | int]]) -> int:
        stored_count = 0
        timestamp = datetime.now(timezone.utc)
        with self.engine.begin() as connection:
            for item in objects:
                file_sha256 = str(item["sha256"])
                existing = connection.execute(
                    sa.select(raw_objects_table.c.sha256).where(raw_objects_table.c.sha256 == file_sha256)
                ).scalar_one_or_none()
                if existing is not None:
                    continue
                content = base64.b64decode(str(item["content_base64"]).encode("ascii"))
                actual_sha256 = sha256(content).hexdigest()
                if actual_sha256 != file_sha256:
                    raise ValueError(
                        f"Raw object sha256 mismatch: expected {file_sha256}, got {actual_sha256}."
                    )
                storage_path = self._get_raw_blob_storage_path(file_sha256)
                if not storage_path.exists():
                    storage_path.parent.mkdir(parents=True, exist_ok=True)
                    storage_path.write_bytes(content)
                connection.execute(
                    raw_objects_table.insert().values(
                        sha256=file_sha256,
                        size_bytes=int(item["size_bytes"]),
                        storage_path=str(storage_path.relative_to(self.storage_root)),
                        created_at=timestamp,
                    )
                )
                stored_count += 1
        return stored_count

    def _get_workspace_row(self, connection: sa.Connection, workspace: str) -> dict[str, object] | None:
        row = connection.execute(
            sa.select(workspaces_table).where(workspaces_table.c.name == workspace)
        ).mappings().first()
        if row is None:
            return None
        return dict(row)

    def _get_revision_manifest(self, connection: sa.Connection, revision_id: str | None) -> dict[str, dict[str, object]]:
        if revision_id is None:
            return {}
        file_rows = connection.execute(
            sa.select(workspace_revision_files_table)
            .where(workspace_revision_files_table.c.revision_id == revision_id)
            .order_by(workspace_revision_files_table.c.path)
        ).mappings()
        manifest: dict[str, dict[str, object]] = {}
        for file_row in file_rows:
            path = str(file_row["path"])
            manifest[path] = {
                "path": path,
                "sha256": str(file_row["sha256"]),
                "size_bytes": int(file_row["size_bytes"]),
                "storage_path": str(file_row["storage_path"]),
            }
        return manifest

    def _get_revision_tree_hash(self, connection: sa.Connection, revision_id: str) -> str:
        row = connection.execute(
            sa.select(workspace_revisions_table.c.tree_hash).where(workspace_revisions_table.c.revision_id == revision_id)
        ).mappings().one()
        return str(row["tree_hash"])

    def _get_blob_storage_path(self, file_sha256: str) -> Path:
        return self.storage_root / "blobs" / file_sha256[:2] / file_sha256[2:4] / file_sha256

    def _get_raw_blob_storage_path(self, file_sha256: str) -> Path:
        return self.storage_root / "raw-blobs" / file_sha256[:2] / file_sha256[2:4] / file_sha256

    def _compute_tree_hash(self, manifest: dict[str, dict[str, object]]) -> str:
        digest = sha256()
        for path in sorted(manifest):
            digest.update(path.encode("utf-8"))
            digest.update(b"\0")
            digest.update(str(manifest[path]["sha256"]).encode("ascii"))
            digest.update(b"\0")
        return digest.hexdigest()

    def _get_raw_current_manifest(
        self, connection: sa.Connection, workspace_id: int
    ) -> dict[str, dict[str, object]]:
        rows = connection.execute(
            sa.select(workspace_raw_current_table)
            .where(workspace_raw_current_table.c.workspace_id == workspace_id)
            .order_by(workspace_raw_current_table.c.path)
        ).mappings()
        manifest: dict[str, dict[str, object]] = {}
        for row in rows:
            path = str(row["path"])
            manifest[path] = {
                "sha256": str(row["sha256"]),
                "size_bytes": int(row["size_bytes"]),
            }
        return manifest

    def _apply_raw_mapping_updates(
        self,
        connection: sa.Connection,
        *,
        workspace_id: int,
        revision_id: str,
        raw_files: list[dict[str, str | int]],
        raw_deleted_paths: list[str],
        current_manifest: dict[str, dict[str, object]],
        timestamp: datetime,
    ) -> None:
        for path in raw_deleted_paths:
            if path not in current_manifest:
                continue
            connection.execute(
                workspace_raw_current_table.delete().where(
                    sa.and_(
                        workspace_raw_current_table.c.workspace_id == workspace_id,
                        workspace_raw_current_table.c.path == path,
                    )
                )
            )
            connection.execute(
                workspace_raw_history_table.insert().values(
                    workspace_id=workspace_id,
                    revision_id=revision_id,
                    path=path,
                    sha256=None,
                    size_bytes=None,
                    action="deleted",
                    created_at=timestamp,
                )
            )

        for item in raw_files:
            path = str(item["path"])
            sha_value = str(item["sha256"])
            size_bytes = int(item["size_bytes"])
            action = "updated" if path in current_manifest else "created"
            connection.execute(
                workspace_raw_current_table.delete().where(
                    sa.and_(
                        workspace_raw_current_table.c.workspace_id == workspace_id,
                        workspace_raw_current_table.c.path == path,
                    )
                )
            )
            connection.execute(
                workspace_raw_current_table.insert().values(
                    workspace_id=workspace_id,
                    path=path,
                    sha256=sha_value,
                    size_bytes=size_bytes,
                    updated_at=timestamp,
                )
            )
            connection.execute(
                workspace_raw_history_table.insert().values(
                    workspace_id=workspace_id,
                    revision_id=revision_id,
                    path=path,
                    sha256=sha_value,
                    size_bytes=size_bytes,
                    action=action,
                    created_at=timestamp,
                )
            )
