from __future__ import annotations

import sqlalchemy as sa

from .schema import raw_objects_table, workspace_raw_current_table, workspace_revision_files_table, workspace_revisions_table, workspaces_table


def get_workspace_row(connection: sa.Connection, workspace: str) -> dict[str, object] | None:
    row = connection.execute(sa.select(workspaces_table).where(workspaces_table.c.name == workspace)).mappings().first()
    return None if row is None else dict(row)


def get_revision_manifest(connection: sa.Connection, revision_id: str | None) -> dict[str, dict[str, object]]:
    if revision_id is None:
        return {}
    rows = connection.execute(sa.select(workspace_revision_files_table).where(workspace_revision_files_table.c.revision_id == revision_id).order_by(workspace_revision_files_table.c.path)).mappings()
    return {str(row["path"]): {"path": str(row["path"]), "sha256": str(row["sha256"]), "size_bytes": int(row["size_bytes"]), "storage_path": str(row["storage_path"])} for row in rows}


def get_revision_tree_hash(connection: sa.Connection, revision_id: str) -> str:
    row = connection.execute(sa.select(workspace_revisions_table.c.tree_hash).where(workspace_revisions_table.c.revision_id == revision_id)).mappings().one()
    return str(row["tree_hash"])


def get_raw_current_manifest(connection: sa.Connection, workspace_id: int) -> dict[str, dict[str, object]]:
    rows = connection.execute(sa.select(workspace_raw_current_table).where(workspace_raw_current_table.c.workspace_id == workspace_id).order_by(workspace_raw_current_table.c.path)).mappings()
    return {str(row["path"]): {"sha256": str(row["sha256"]), "size_bytes": int(row["size_bytes"])} for row in rows}


def raw_object_exists(connection: sa.Connection, file_sha256: str):
    return connection.execute(sa.select(raw_objects_table.c.sha256).where(raw_objects_table.c.sha256 == file_sha256)).scalar_one_or_none()
