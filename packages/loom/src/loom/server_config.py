from __future__ import annotations

import json
import os
from pathlib import Path


DEFAULT_SERVER_URL = "https://loom-api-free.onrender.com"
_server_base_url_override: str | None = None
_CONFIG_KEY = "server_url"


def set_base_url(base_url: str | None) -> None:
    global _server_base_url_override
    _server_base_url_override = _normalize_base_url(base_url)


def persist_base_url(base_url: str) -> str:
    normalized = _normalize_base_url(base_url)
    if normalized is None:
        raise ValueError("Base URL must not be empty.")
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps({_CONFIG_KEY: normalized}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return normalized


def get_base_url() -> str:
    override = _normalize_base_url(_server_base_url_override)
    if override is not None:
        return override
    env_value = _normalize_base_url(os.environ.get("LOOM_SERVER_URL"))
    if env_value is not None:
        return env_value
    stored_value = _normalize_base_url(_load_persisted_base_url())
    if stored_value is not None:
        return stored_value
    return DEFAULT_SERVER_URL


def resolve_base_url(base_url: str | None) -> str:
    explicit = _normalize_base_url(base_url)
    if explicit is not None:
        return explicit
    return get_base_url()


def _normalize_base_url(base_url: str | None) -> str | None:
    if base_url is None:
        return None
    normalized = base_url.strip().rstrip("/")
    return normalized or None


def get_config_path() -> Path:
    if os.environ.get("LOOM_CONFIG_HOME"):
        return Path(os.environ["LOOM_CONFIG_HOME"]).expanduser().resolve() / "config.json"
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")).expanduser().resolve()
    return config_home / "loom" / "config.json"


def _load_persisted_base_url() -> str | None:
    config_path = get_config_path()
    if not config_path.exists():
        return None
    data = json.loads(config_path.read_text(encoding="utf-8"))
    value = data.get(_CONFIG_KEY)
    return str(value) if isinstance(value, str) else None
