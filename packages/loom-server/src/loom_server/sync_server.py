from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .sync_service import LoomSyncService, WorkspaceConflictError, WorkspaceNotFoundError


class PushFilePayload(BaseModel):
    path: str
    sha256: str
    size_bytes: int
    content_base64: str


class RawObjectPayload(BaseModel):
    sha256: str
    size_bytes: int
    content_base64: str


class RawExistsRequest(BaseModel):
    hashes: list[str]


class RawUploadRequest(BaseModel):
    objects: list[RawObjectPayload]


class PushWorkspaceRequest(BaseModel):
    base_revision: str | None = None
    local_commit: str | None = None
    tree_hash: str
    message: str = Field(default="Push workspace to Loom server")
    files: list[PushFilePayload]
    deleted_paths: list[str] = Field(default_factory=list)
    raw_files: list[PushFilePayload] = Field(default_factory=list)
    raw_deleted_paths: list[str] = Field(default_factory=list)


def create_app(
    database_url: str,
    storage_root: Path | str,
    *,
    workspace_root: Path | str | None = None,
    cors_origins: list[str] | None = None,
) -> FastAPI:
    service = LoomSyncService(database_url=database_url, storage_root=storage_root)
    service.init_db()

    app = FastAPI(title="Loom Sync Server", version="0.1.0")
    allowed_origins = cors_origins or _parse_cors_origins(os.environ.get("LOOM_SERVER_CORS_ORIGINS"))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.sync_service = service
    default_workspace_root = Path(storage_root).resolve().parent
    resolved_workspace_root = Path(workspace_root if workspace_root is not None else default_workspace_root).resolve()
    app.state.workspace_root = resolved_workspace_root

    @app.get("/health")
    def health() -> dict[str, bool]:
        return {"ok": True}

    @app.get("/api/workspaces")
    def list_workspaces() -> dict[str, list[dict[str, str | None]]]:
        return {"workspaces": service.list_workspaces()}

    @app.post("/api/raw/exists")
    def raw_exists(request: RawExistsRequest) -> dict[str, list[str]]:
        return {"missing_hashes": service.get_missing_raw_hashes(request.hashes)}

    @app.post("/api/raw/objects")
    def upload_raw_objects(request: RawUploadRequest) -> dict[str, int]:
        return {"stored_count": service.store_raw_objects([item.model_dump() for item in request.objects])}

    @app.get("/api/raw/objects/{file_sha256}")
    def get_raw_object(file_sha256: str) -> dict[str, str | int]:
        try:
            return service.get_raw_object(file_sha256)
        except WorkspaceNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get("/api/explore/workspaces")
    def list_explore_workspaces() -> dict[str, list[dict[str, object]]]:
        return {"workspaces": service.list_explore_workspaces()}

    @app.get("/api/explore/workspaces/{workspace}")
    def get_explore_workspace(workspace: str) -> dict[str, object]:
        try:
            return service.get_explore_workspace(workspace)
        except WorkspaceNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get("/api/workspaces/{workspace}")
    def get_workspace_head(workspace: str) -> dict[str, str | None]:
        try:
            return service.get_workspace_head(workspace)
        except WorkspaceNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get("/api/workspaces/{workspace}/raw-manifest")
    def get_workspace_raw_manifest(workspace: str) -> dict[str, object]:
        try:
            return {
                "workspace": workspace,
                "raw_manifest": service.get_workspace_raw_manifest(workspace),
            }
        except WorkspaceNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.get("/api/workspaces/{workspace}/pull")
    def pull_workspace(workspace: str, base_revision: str | None = None) -> dict[str, object]:
        try:
            return service.pull_workspace(workspace, base_revision=base_revision)
        except WorkspaceNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    @app.post("/api/workspaces/{workspace}/push")
    def push_workspace(workspace: str, request: PushWorkspaceRequest) -> dict[str, object]:
        try:
            return service.push_workspace(
                workspace,
                base_revision=request.base_revision,
                local_commit=request.local_commit,
                tree_hash=request.tree_hash,
                message=request.message,
                files=[item.model_dump() for item in request.files],
                deleted_paths=request.deleted_paths,
                raw_files=[item.model_dump() for item in request.raw_files],
                raw_deleted_paths=request.raw_deleted_paths,
            )
        except WorkspaceConflictError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    return app


def _parse_cors_origins(value: str | None) -> list[str]:
    if value is None:
        return ["*"]
    origins = [item.strip() for item in value.split(",") if item.strip()]
    return origins or ["*"]
