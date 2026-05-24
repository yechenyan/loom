from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class ScanRequest:
    topic: str
    original_message: str


_SCAN_PATTERNS = (
    re.compile(r"(?i)(?:^|\b)loom\s+scan\s+(?P<topic>[a-z0-9][a-z0-9_./-]*)\b"),
    re.compile(
        r"(?i)(?:^|\b)(?:please\s+)?scan\s+(?P<topic>[a-z0-9][a-z0-9_./-]*)\s+with\s+loom\b"
    ),
)


def is_fast_scan_command(message: str) -> bool:
    normalized = message.strip()
    if not normalized:
        return False

    lowered = normalized.lower()
    return lowered.startswith("loom scan ") and len(normalized) > len("loom scan ")


def parse_chat_request(message: str) -> ScanRequest | None:
    normalized = message.strip()
    if not normalized:
        return None

    fast_request = _parse_fast_scan_command(normalized, message)
    if fast_request is not None:
        return fast_request

    for pattern in _SCAN_PATTERNS:
        match = pattern.search(normalized)
        if match:
            return ScanRequest(
                topic=match.group("topic").strip().strip("/"),
                original_message=message,
            )

    return None


def _parse_fast_scan_command(normalized: str, original_message: str) -> ScanRequest | None:
    parts = normalized.split(None, 2)
    if len(parts) < 3:
        return None

    if parts[0].lower() != "loom" or parts[1].lower() != "scan":
        return None

    topic = parts[2].strip().strip("/").split()[0]
    if not re.fullmatch(r"[a-z0-9][a-z0-9_./-]*", topic, flags=re.IGNORECASE):
        return None

    return ScanRequest(topic=topic, original_message=original_message)
