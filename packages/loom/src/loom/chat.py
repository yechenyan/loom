from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class LoomCommandRequest:
    command: str
    workspace: str | None
    source_path: str | None
    query: str | None
    original_message: str


@dataclass(frozen=True)
class ScanRequest:
    source_path: str | None
    workspace: str | None
    original_message: str


_WORKSPACE_PATTERN = r"[a-z0-9][a-z0-9_./-]*"
_GENERIC_PATTERNS = (
    re.compile(rf"(?i)(?:^|\b)loom\s+(?P<command>confirm|push|pull|status)(?:\s+(?P<workspace>{_WORKSPACE_PATTERN}))?\b"),
)
_RESERVED_NON_ASK_WORDS = {
    "ask",
    "confirm",
    "get",
    "init",
    "install",
    "pull",
    "pull-raw",
    "push",
    "scan",
    "server-init-db",
    "server-run",
    "set-api",
    "status",
}


def is_fast_scan_command(message: str) -> bool:
    normalized = message.strip()
    if not normalized:
        return False

    lowered = normalized.lower()
    return (
        lowered.startswith("loom scan ") and len(normalized) > len("loom scan ")
    ) or (
        lowered.startswith("/loom-scan ") and len(normalized) > len("/loom-scan ")
    )


def parse_chat_request(message: str) -> ScanRequest | None:
    command_request = parse_loom_command(message)
    if command_request is None or command_request.command != "scan":
        return None
    return ScanRequest(
        source_path=command_request.source_path,
        workspace=command_request.workspace,
        original_message=message,
    )


def parse_loom_command(message: str) -> LoomCommandRequest | None:
    normalized = message.strip()
    if not normalized:
        return None

    fast_request = _parse_fast_scan_command(normalized, message)
    if fast_request is not None:
        return fast_request

    looser_request = _parse_loose_scan_command(normalized, message)
    if looser_request is not None:
        return looser_request

    for pattern in _GENERIC_PATTERNS:
        match = pattern.search(normalized)
        if match:
            return LoomCommandRequest(
                command=match.group("command").lower(),
                workspace=_normalize_workspace(match.group("workspace")),
                source_path=None,
                query=None,
                original_message=message,
            )

    ask_request = _parse_ask_command(normalized, message)
    if ask_request is not None:
        return ask_request

    return None


def _parse_fast_scan_command(normalized: str, original_message: str) -> LoomCommandRequest | None:
    if normalized.lower().startswith("/loom-scan "):
        source_path, workspace = _split_scan_target(normalized[len("/loom-scan ") :].strip())
        if source_path is None:
            return None
        return LoomCommandRequest(
            command="scan",
            workspace=workspace,
            source_path=source_path,
            query=None,
            original_message=original_message,
        )

    parts = normalized.split(None, 2)
    if len(parts) < 2:
        return None

    if parts[0].lower() != "loom" or parts[1].lower() != "scan":
        return None

    source_path = None
    workspace = None
    if len(parts) == 3:
        source_path, workspace = _split_scan_target(parts[2].strip())
        if source_path is None:
            return None

    return LoomCommandRequest(command="scan", workspace=workspace, source_path=source_path, query=None, original_message=original_message)


def _parse_loose_scan_command(normalized: str, original_message: str) -> LoomCommandRequest | None:
    match = re.search(r"(?i)(?:^|\b)(?:please\s+)?scan\s+(?P<target>.+?)\s+with\s+loom(?:\b|$)", normalized)
    if not match:
        return None
    source_path, workspace = _split_scan_target(match.group("target").strip())
    if source_path is None:
        return None
    return LoomCommandRequest(command="scan", workspace=workspace, source_path=source_path, query=None, original_message=original_message)


def _parse_ask_command(normalized: str, original_message: str) -> LoomCommandRequest | None:
    if normalized.lower().startswith("/loom-ask "):
        query = normalized[len("/loom-ask ") :].strip()
        return LoomCommandRequest(
            command="ask",
            workspace=None,
            source_path=None,
            query=query or None,
            original_message=original_message,
        )
    if normalized.lower().startswith("loom ask "):
        query = normalized[len("loom ask ") :].strip()
        return LoomCommandRequest(command="ask", workspace=None, source_path=None, query=query or None, original_message=original_message)
    if not normalized.lower().startswith("loom "):
        return None
    query = normalized[len("loom ") :].strip()
    if not query:
        return None
    first_word = query.split()[0].lower()
    if first_word in _RESERVED_NON_ASK_WORDS:
        return None
    return LoomCommandRequest(command="ask", workspace=None, source_path=None, query=query, original_message=original_message)


def _split_scan_target(value: str) -> tuple[str | None, str | None]:
    normalized = value.strip()
    if not normalized:
        return None, None

    match = re.fullmatch(rf"(?P<source>.+?)(?:\s+to\s+(?P<workspace>{_WORKSPACE_PATTERN}))?", normalized, flags=re.IGNORECASE)
    if not match:
        return None, None

    source_path = _normalize_source_path(match.group("source"))
    workspace = _normalize_workspace(match.group("workspace"))
    if source_path is None:
        return None, None
    return source_path, workspace


def _normalize_workspace(value: str | None) -> str | None:
    if value is None:
        return None
    return value.strip().strip("/") or None


def _normalize_source_path(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) >= 2 and normalized[0] == normalized[-1] and normalized[0] in {"`", "'", '"'}:
        normalized = normalized[1:-1].strip()
    return normalized or None
