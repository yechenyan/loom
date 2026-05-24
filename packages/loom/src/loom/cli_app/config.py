from __future__ import annotations

import os


DEFAULT_SERVER_URL = os.environ.get("LOOM_SERVER_URL", "http://127.0.0.1:8765")
DEFAULT_DATABASE_URL = os.environ.get(
    "LOOM_SERVER_DATABASE_URL",
    "postgresql+psycopg2://loom@127.0.0.1:5432/loom",
)
