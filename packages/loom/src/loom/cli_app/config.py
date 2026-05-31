from __future__ import annotations

import os

from ..server_config import get_base_url


DEFAULT_SERVER_URL = get_base_url()
DEFAULT_DATABASE_URL = os.environ.get(
    "LOOM_SERVER_DATABASE_URL",
    "postgresql+psycopg2://loom@127.0.0.1:5432/loom",
)
DEFAULT_SERVER_HOST = os.environ.get(
    "LOOM_SERVER_HOST",
    "0.0.0.0" if os.environ.get("RENDER") or os.environ.get("PORT") else "127.0.0.1",
)
DEFAULT_SERVER_PORT = int(os.environ.get("PORT", os.environ.get("LOOM_SERVER_PORT", "8765")))
DEFAULT_SERVER_WORKSPACE_ROOT = os.environ.get("LOOM_SERVER_WORKSPACE_ROOT")
