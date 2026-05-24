from __future__ import annotations

from datetime import datetime

import sqlalchemy as sa

from .schema import workspace_raw_current_table, workspace_raw_history_table


def apply_raw_mapping_updates(connection: sa.Connection, *, workspace_id: int, revision_id: str, raw_files, raw_deleted_paths, current_manifest, timestamp: datetime) -> None:
    for path in raw_deleted_paths:
        if path not in current_manifest:
            continue
        connection.execute(workspace_raw_current_table.delete().where(sa.and_(workspace_raw_current_table.c.workspace_id == workspace_id, workspace_raw_current_table.c.path == path)))
        connection.execute(workspace_raw_history_table.insert().values(workspace_id=workspace_id, revision_id=revision_id, path=path, sha256=None, size_bytes=None, action="deleted", created_at=timestamp))
    for item in raw_files:
        path = str(item["path"])
        connection.execute(workspace_raw_current_table.delete().where(sa.and_(workspace_raw_current_table.c.workspace_id == workspace_id, workspace_raw_current_table.c.path == path)))
        connection.execute(workspace_raw_current_table.insert().values(workspace_id=workspace_id, path=path, sha256=str(item["sha256"]), size_bytes=int(item["size_bytes"]), updated_at=timestamp))
        connection.execute(workspace_raw_history_table.insert().values(workspace_id=workspace_id, revision_id=revision_id, path=path, sha256=str(item["sha256"]), size_bytes=int(item["size_bytes"]), action="updated" if path in current_manifest else "created", created_at=timestamp))
