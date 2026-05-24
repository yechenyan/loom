from __future__ import annotations

import os


DEFAULT_LOCAL_SERVER_URL = "http://127.0.0.1:8765"
_server_base_url_override: str | None = None


def set_base_url(base_url: str | None) -> None:
    global _server_base_url_override
    _server_base_url_override = _normalize_base_url(base_url)


def get_base_url() -> str:
    override = _normalize_base_url(_server_base_url_override)
    if override is not None:
        return override
    env_value = _normalize_base_url(os.environ.get("LOOM_SERVER_URL"))
    if env_value is not None:
        return env_value
    return DEFAULT_LOCAL_SERVER_URL


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
