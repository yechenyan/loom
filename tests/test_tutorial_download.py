from __future__ import annotations

import hashlib
import io
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

from loom.cli_app.tutorial_download import (  # noqa: E402
    TUTORIAL_DATASET_NAME,
    TutorialInstallError,
    install_tutorial_dataset,
)


class TutorialDownloadTest(unittest.TestCase):
    def test_installs_verified_archive_from_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive = root / "demo.tar.gz"
            _write_archive(archive, {"loom.md": "# Demo\n", "data.csv": "a,b\n1,2\n"})
            digest = hashlib.sha256(archive.read_bytes()).hexdigest()

            result = install_tutorial_dataset(root / "workspace", url=archive.as_uri(), sha256=digest)

            self.assertFalse(result.skipped)
            self.assertTrue((root / "workspace" / "raw_data" / TUTORIAL_DATASET_NAME / "loom.md").exists())
            self.assertTrue((root / "workspace" / "raw_data" / TUTORIAL_DATASET_NAME / "data.csv").exists())

    def test_skips_existing_dataset_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            existing = root / "workspace" / "raw_data" / TUTORIAL_DATASET_NAME
            existing.mkdir(parents=True)
            (existing / "loom.md").write_text("# Existing\n", encoding="utf-8")

            result = install_tutorial_dataset(root / "workspace", url=(root / "missing.tar.gz").as_uri())

            self.assertTrue(result.skipped)
            self.assertEqual((existing / "loom.md").read_text(encoding="utf-8"), "# Existing\n")

    def test_checksum_mismatch_does_not_leave_target_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive = root / "demo.tar.gz"
            _write_archive(archive, {"loom.md": "# Demo\n"})

            with self.assertRaises(TutorialInstallError):
                install_tutorial_dataset(root / "workspace", url=archive.as_uri(), sha256="0" * 64)

            self.assertFalse((root / "workspace" / "raw_data" / TUTORIAL_DATASET_NAME).exists())

    def test_custom_url_requires_custom_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive = root / "demo.tar.gz"
            _write_archive(archive, {"loom.md": "# Demo\n"})

            with self.assertRaises(TutorialInstallError):
                install_tutorial_dataset(root / "workspace", url=archive.as_uri())

    def test_rejects_unsafe_archive_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive = root / "bad.tar.gz"
            with tarfile.open(archive, "w:gz") as tar:
                payload = b"bad"
                info = tarfile.TarInfo("../escape.txt")
                info.size = len(payload)
                tar.addfile(info, io.BytesIO(payload))

            with self.assertRaises(TutorialInstallError):
                install_tutorial_dataset(root / "workspace", url=archive.as_uri(), sha256="")

    def test_rejects_special_archive_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            archive = root / "bad.tar.gz"
            with tarfile.open(archive, "w:gz") as tar:
                fifo = tarfile.TarInfo(f"{TUTORIAL_DATASET_NAME}/fifo")
                fifo.type = tarfile.FIFOTYPE
                tar.addfile(fifo)

            with self.assertRaises(TutorialInstallError):
                install_tutorial_dataset(root / "workspace", url=archive.as_uri(), sha256="")


def _write_archive(path: Path, files: dict[str, str]) -> None:
    with tarfile.open(path, "w:gz") as tar:
        for name, content in files.items():
            payload = content.encode("utf-8")
            info = tarfile.TarInfo(f"{TUTORIAL_DATASET_NAME}/{name}")
            info.size = len(payload)
            tar.addfile(info, io.BytesIO(payload))


if __name__ == "__main__":
    unittest.main()
