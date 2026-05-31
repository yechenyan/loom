from __future__ import annotations

import hashlib
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_SRC = ROOT / "packages" / "loom" / "src"
TUTORIAL_ARCHIVE = ROOT / "dist" / "demo_germany_energy_data.tar.gz"
TUTORIAL_SOURCE = ROOT / "raw_example" / "demo_germany_energy_data"
DOWNLOAD_TIMEOUT_SECONDS = 30

if str(PACKAGE_SRC) not in sys.path:
    sys.path.insert(0, str(PACKAGE_SRC))

from loom.cli_app.tutorial_download import (  # noqa: E402
    TUTORIAL_DATA_SHA256,
    TUTORIAL_DATA_URL,
    TUTORIAL_DATA_VERSION,
)

from build_tutorial_data import build_archive_bytes  # noqa: E402


class ReleaseCheckError(RuntimeError):
    """Raised when a release preflight check fails."""


@dataclass(frozen=True)
class TutorialAssetCheck:
    url: str
    version: str
    archive_path: Path
    sha256: str
    size_bytes: int


def verify_tutorial_release_asset() -> TutorialAssetCheck:
    archive_path = build_tutorial_archive()
    local_sha256 = _sha256_file(archive_path)
    if local_sha256 != TUTORIAL_DATA_SHA256:
        raise ReleaseCheckError(
            "Tutorial archive SHA256 does not match the CLI config.\n"
            f"Archive: {archive_path}\n"
            f"Archive SHA256: {local_sha256}\n"
            f"Configured SHA256: {TUTORIAL_DATA_SHA256}\n"
            "Update TUTORIAL_DATA_SHA256 before publishing."
        )

    try:
        remote_sha256, remote_size = _download_sha256(TUTORIAL_DATA_URL)
    except Exception as exc:  # pragma: no cover - exact urllib errors vary
        raise ReleaseCheckError(
            "Tutorial archive URL is not downloadable.\n"
            f"URL: {TUTORIAL_DATA_URL}\n"
            f"Built archive: {archive_path}\n"
            f"Reference tag: {TUTORIAL_DATA_VERSION}\n"
            "Push the built archive to the repository path for this tag before publishing PyPI."
        ) from exc

    if remote_sha256 != TUTORIAL_DATA_SHA256:
        raise ReleaseCheckError(
            "Tutorial release asset SHA256 does not match the CLI config.\n"
            f"URL: {TUTORIAL_DATA_URL}\n"
            f"Remote SHA256: {remote_sha256}\n"
            f"Configured SHA256: {TUTORIAL_DATA_SHA256}\n"
            "Push the matching archive or update the CLI config before publishing."
        )

    return TutorialAssetCheck(
        url=TUTORIAL_DATA_URL,
        version=TUTORIAL_DATA_VERSION,
        archive_path=archive_path,
        sha256=remote_sha256,
        size_bytes=remote_size,
    )


def build_tutorial_archive() -> Path:
    if not (TUTORIAL_SOURCE / "loom.md").exists():
        raise ReleaseCheckError(f"Missing tutorial source data: {TUTORIAL_SOURCE}")
    archive_bytes = build_archive_bytes(TUTORIAL_SOURCE)
    TUTORIAL_ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    TUTORIAL_ARCHIVE.write_bytes(archive_bytes)
    return TUTORIAL_ARCHIVE


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _download_sha256(url: str) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
    return digest.hexdigest(), size
