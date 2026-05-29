from __future__ import annotations

import argparse
import os
from pathlib import Path

import psycopg2
import sqlalchemy as sa

from .sync_server import create_app


DEFAULT_DATABASE_URL = os.environ.get(
    "LOOM_SERVER_DATABASE_URL",
    "postgresql+psycopg2://loom@127.0.0.1:5432/loom",
)
DEFAULT_STORAGE_ROOT = Path(os.environ.get("LOOM_SERVER_STORAGE_ROOT", Path.cwd() / ".loom-server-storage"))
DEFAULT_WORKSPACE_ROOT = Path(os.environ.get("LOOM_SERVER_WORKSPACE_ROOT", Path.cwd()))
DEFAULT_HOST = os.environ.get(
    "LOOM_SERVER_HOST",
    "0.0.0.0" if os.environ.get("RENDER") or os.environ.get("PORT") else "127.0.0.1",
)
DEFAULT_PORT = int(os.environ.get("PORT", os.environ.get("LOOM_SERVER_PORT", "8765")))


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "init-db":
        return run_init_db(args.database_url, args.storage_root, args.workspace_root)
    if args.command == "run":
        return run_server(args.database_url, args.storage_root, args.workspace_root, args.host, args.port)

    parser.print_help()
    return 1


def run_init_db(database_url: str, storage_root: Path | str, workspace_root: Path | str) -> int:
    _ensure_database_exists(database_url)
    app = create_app(database_url, storage_root, workspace_root=workspace_root)
    app.state.sync_service.init_db()
    print(f"Initialized Loom sync database: {database_url}")
    print(f"Storage root: {storage_root}")
    print(f"Workspace root: {workspace_root}")
    return 0


def run_server(
    database_url: str,
    storage_root: Path | str,
    workspace_root: Path | str,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> int:
    import uvicorn

    _ensure_database_exists(database_url)
    app = create_app(database_url, storage_root, workspace_root=workspace_root)
    uvicorn.run(app, host=host, port=port)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="loom-server")
    subparsers = parser.add_subparsers(dest="command")

    init_db_parser = subparsers.add_parser("init-db", help="Initialize the Loom sync server database schema.")
    init_db_parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help="SQLAlchemy database URL for the Loom sync server.",
    )
    init_db_parser.add_argument(
        "--storage-root",
        type=Path,
        default=DEFAULT_STORAGE_ROOT,
        help="Filesystem root where server snapshots are stored.",
    )
    init_db_parser.add_argument(
        "--workspace-root",
        type=Path,
        default=DEFAULT_WORKSPACE_ROOT,
        help="Workspace root that contains loom/.",
    )

    run_parser = subparsers.add_parser("run", help="Run the Loom sync FastAPI server.")
    run_parser.add_argument(
        "--database-url",
        default=DEFAULT_DATABASE_URL,
        help="SQLAlchemy database URL for the Loom sync server.",
    )
    run_parser.add_argument(
        "--storage-root",
        type=Path,
        default=DEFAULT_STORAGE_ROOT,
        help="Filesystem root where server snapshots are stored.",
    )
    run_parser.add_argument(
        "--workspace-root",
        type=Path,
        default=DEFAULT_WORKSPACE_ROOT,
        help="Workspace root that contains loom/.",
    )
    run_parser.add_argument("--host", default=DEFAULT_HOST, help="Host to bind the FastAPI server to.")
    run_parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Port to bind the FastAPI server to.")

    return parser


def _ensure_database_exists(database_url: str) -> None:
    url = sa.engine.make_url(database_url)
    if not str(url.drivername).startswith("postgresql"):
        return

    database_name = url.database
    if not database_name:
        return

    maintenance_database = "postgres"
    connect_kwargs = {
        "dbname": maintenance_database,
        "user": url.username,
        "password": url.password,
        "host": url.host,
        "port": url.port,
    }
    connect_kwargs = {key: value for key, value in connect_kwargs.items() if value is not None}

    with psycopg2.connect(**connect_kwargs) as connection:
        connection.autocommit = True
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (database_name,))
            exists = cursor.fetchone() is not None
            if not exists:
                cursor.execute(f'CREATE DATABASE "{database_name}"')
