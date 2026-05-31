from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "loom" / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import release_checks  # noqa: E402


class ReleaseChecksTest(unittest.TestCase):
    def test_tutorial_asset_check_requires_downloadable_matching_asset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = _write_tutorial_source(root)
            archive_path = root / "dist" / "demo_germany_energy_data.tar.gz"
            archive_bytes = release_checks.build_archive_bytes(source)
            digest = hashlib.sha256(archive_bytes).hexdigest()

            with _patch_tutorial_config(source, archive_path, digest):
                with mock.patch("release_checks.urllib.request.urlopen", return_value=_Response(archive_bytes)):
                    result = release_checks.verify_tutorial_release_asset()

            self.assertEqual(result.sha256, digest)
            self.assertEqual(result.size_bytes, len(archive_bytes))
            self.assertEqual(archive_path.read_bytes(), archive_bytes)

    def test_tutorial_asset_check_fails_when_remote_asset_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = _write_tutorial_source(root)
            archive_path = root / "dist" / "demo_germany_energy_data.tar.gz"
            digest = hashlib.sha256(release_checks.build_archive_bytes(source)).hexdigest()

            with _patch_tutorial_config(source, archive_path, digest):
                with mock.patch("release_checks.urllib.request.urlopen", side_effect=OSError("404")):
                    with self.assertRaisesRegex(
                        release_checks.ReleaseCheckError,
                        "Tutorial archive URL is not downloadable",
                    ):
                        release_checks.verify_tutorial_release_asset()


def _write_tutorial_source(root: Path) -> Path:
    source = root / "demo_germany_energy_data"
    source.mkdir()
    (source / "loom.md").write_text("# Demo\n", encoding="utf-8")
    (source / "data.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    return source


def _patch_tutorial_config(source: Path, archive_path: Path, digest: str):
    return mock.patch.multiple(
        release_checks,
        TUTORIAL_SOURCE=source,
        TUTORIAL_ARCHIVE=archive_path,
        TUTORIAL_DATA_SHA256=digest,
        TUTORIAL_DATA_URL="https://example.com/demo_germany_energy_data.tar.gz",
        TUTORIAL_DATA_VERSION="demo-data-test",
    )


class _Response:
    def __init__(self, data: bytes) -> None:
        self._data = data
        self._offset = 0

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self, size: int = -1) -> bytes:
        if size < 0:
            size = len(self._data) - self._offset
        chunk = self._data[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


if __name__ == "__main__":
    unittest.main()
