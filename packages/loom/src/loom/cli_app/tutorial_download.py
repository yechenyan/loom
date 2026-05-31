from __future__ import annotations

import hashlib
import shutil
import tarfile
import tempfile
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from ..raw_cache_support import resolve_raw_data_root


TUTORIAL_DATASET_NAME = "demo_germany_energy_data"
TUTORIAL_DATA_VERSION = "demo-data-v1"
TUTORIAL_DATA_URL = (
    "https://raw.githubusercontent.com/yechenyan/loom/"
    f"{TUTORIAL_DATA_VERSION}/tutorial-data/demo_germany_energy_data.tar.gz"
)
TUTORIAL_DATA_SHA256 = "d2065bf28988d3ba8c992a126044edb69821a20909ba2177ee5a78fd60a577fc"
DOWNLOAD_TIMEOUT_SECONDS = 20


class TutorialInstallError(RuntimeError):
    pass


@dataclass(frozen=True)
class TutorialInstallResult:
    path: Path
    skipped: bool = False


def install_tutorial_dataset(
    workspace_root: Path,
    *,
    url: str | None = None,
    sha256: str | None = None,
    force: bool = False,
) -> TutorialInstallResult:
    target_dir = resolve_raw_data_root(workspace_root) / TUTORIAL_DATASET_NAME
    if target_dir.exists() and not force:
        return TutorialInstallResult(target_dir, skipped=True)

    if url is not None and sha256 is None:
        raise TutorialInstallError("`--tutorial-url` requires `--tutorial-sha256`.")

    source_url = url or TUTORIAL_DATA_URL
    expected_sha256 = sha256 if sha256 is not None else TUTORIAL_DATA_SHA256
    with tempfile.TemporaryDirectory(prefix="loom-tutorial-") as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        archive_path = temp_dir / "tutorial.tar.gz"
        extract_dir = temp_dir / "extract"
        _download(source_url, archive_path)
        _verify_sha256(archive_path, expected_sha256)
        _extract_safe(archive_path, extract_dir)
        source_dir = _find_dataset_dir(extract_dir)
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        if force and target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.move(str(source_dir), str(target_dir))
    return TutorialInstallResult(target_dir)


def install_tutorial_or_warn(
    workspace_root: Path,
    *,
    url: str | None,
    sha256: str | None,
    force: bool,
) -> None:
    try:
        result = install_tutorial_dataset(workspace_root, url=url, sha256=sha256, force=force)
    except TutorialInstallError as exc:
        print(f"Tutorial data was not installed: {exc}")
        print("You can retry later with `loomcli init --agent codex` or provide `--tutorial-url` and `--tutorial-sha256`.")
        return
    if result.skipped:
        print(f"Tutorial data already exists at: {result.path}")
        print("Use `--force-tutorial` to replace it.")
        return
    print(f"Tutorial data installed at: {result.path}")


def _download(url: str, archive_path: Path) -> None:
    try:
        with urllib.request.urlopen(url, timeout=DOWNLOAD_TIMEOUT_SECONDS) as response:
            archive_path.write_bytes(response.read())
    except Exception as exc:  # pragma: no cover - exact urllib errors vary by platform
        raise TutorialInstallError(f"Could not download tutorial data from {url}: {exc}") from exc


def _verify_sha256(path: Path, expected_sha256: str) -> None:
    if not expected_sha256:
        return
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != expected_sha256:
        raise TutorialInstallError(
            f"Tutorial data checksum mismatch: expected {expected_sha256}, got {digest}."
        )


def _extract_safe(archive_path: Path, extract_dir: Path) -> None:
    extract_dir.mkdir(parents=True, exist_ok=True)
    try:
        with tarfile.open(archive_path, "r:gz") as archive:
            for member in archive.getmembers():
                if member.issym() or member.islnk():
                    raise TutorialInstallError(f"Unsafe tutorial archive link: {member.name}")
                if not (member.isfile() or member.isdir()):
                    raise TutorialInstallError(f"Unsupported tutorial archive entry: {member.name}")
                target_path = (extract_dir / member.name).resolve()
                if not target_path.is_relative_to(extract_dir.resolve()):
                    raise TutorialInstallError(f"Unsafe tutorial archive path: {member.name}")
            archive.extractall(extract_dir)
    except tarfile.TarError as exc:
        raise TutorialInstallError(f"Could not unpack tutorial data: {exc}") from exc


def _find_dataset_dir(extract_dir: Path) -> Path:
    direct = extract_dir / TUTORIAL_DATASET_NAME
    if (direct / "loom.md").exists():
        return direct
    if (extract_dir / "loom.md").exists():
        return extract_dir
    candidates = [path for path in extract_dir.iterdir() if (path / "loom.md").exists()]
    if len(candidates) == 1:
        return candidates[0]
    raise TutorialInstallError("Tutorial archive must contain exactly one dataset with loom.md.")
