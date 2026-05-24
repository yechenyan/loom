from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class LoomCommandRequest:
    command: str
    workspace: str | None
    original_message: str


@dataclass(frozen=True)
class ScanRequest:
    topic: str
    original_message: str


_WORKSPACE_PATTERN = r"[a-z0-9][a-z0-9_./-]*"
_SCAN_PATTERNS = (
    re.compile(rf"(?i)(?:^|\b)loom\s+scan\s+(?P<workspace>{_WORKSPACE_PATTERN})\b"),
    re.compile(rf"(?i)(?:^|\b)(?:please\s+)?scan\s+(?P<workspace>{_WORKSPACE_PATTERN})\s+with\s+loom\b"),
)
_GENERIC_PATTERNS = (
    re.compile(rf"(?i)(?:^|\b)loom\s+(?P<command>confirm|push|pull|status)(?:\s+(?P<workspace>{_WORKSPACE_PATTERN}))?\b"),
)


def is_fast_scan_command(message: str) -> bool:
    normalized = message.strip()
    if not normalized:
        return False

    lowered = normalized.lower()
    return lowered.startswith("loom scan ") and len(normalized) > len("loom scan ")


def parse_chat_request(message: str) -> ScanRequest | None:
    command_request = parse_loom_command(message)
    if command_request is None or command_request.command != "scan" or command_request.workspace is None:
        return None
    return ScanRequest(topic=command_request.workspace, original_message=message)


def parse_loom_command(message: str) -> LoomCommandRequest | None:
    normalized = message.strip()
    if not normalized:
        return None

    fast_request = _parse_fast_scan_command(normalized, message)
    if fast_request is not None:
        return fast_request

    for pattern in _SCAN_PATTERNS:
        match = pattern.search(normalized)
        if match:
            return LoomCommandRequest(
                command="scan",
                workspace=_normalize_workspace(match.group("workspace")),
                original_message=message,
            )

    for pattern in _GENERIC_PATTERNS:
        match = pattern.search(normalized)
        if match:
            return LoomCommandRequest(
                command=match.group("command").lower(),
                workspace=_normalize_workspace(match.group("workspace")),
                original_message=message,
            )

    return None


def _parse_fast_scan_command(normalized: str, original_message: str) -> LoomCommandRequest | None:
    parts = normalized.split(None, 2)
    if len(parts) < 3:
        return None

    if parts[0].lower() != "loom" or parts[1].lower() != "scan":
        return None

    workspace = parts[2].strip().strip("/").split()[0]
    if not re.fullmatch(_WORKSPACE_PATTERN, workspace, flags=re.IGNORECASE):
        return None

    return LoomCommandRequest(command="scan", workspace=workspace, original_message=original_message)


def _normalize_workspace(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().strip("/") or None
