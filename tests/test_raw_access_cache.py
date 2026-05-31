from __future__ import annotations

import base64
from hashlib import sha256
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

import loom
from loom.raw_snapshot import build_raw_workspace_snapshot
from loom_server.sync_server import create_app
from loom_server.service_parts.helpers import raw_blob_storage_path

from .support import LoomTestCase


class RawAccessCacheTest(LoomTestCase):
    def test_get_links_existing_local_raw_file_without_remote_download(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            raw_file = self.write_energy_dataset(workspace_root)
            self.assertEqual(self.call_main([*self.scan_command(), "--workspace-root", str(workspace_root)])[0], 0)
            local_path = loom.get("energy/technology-data/costs.csv", workspace_root=workspace_root)
            self.assertEqual(local_path.read_text(encoding="utf-8"), raw_file.read_text(encoding="utf-8"))
            self.assertTrue(local_path.exists())

    def test_get_links_local_raw_file_from_recorded_scan_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            dataset_dir = workspace_root / "raw_data" / "cost"
            dataset_dir.mkdir(parents=True, exist_ok=True)
            (dataset_dir / "loom.md").write_text("source: https://example.com/cost\n\nCost dataset", encoding="utf-8")
            raw_file = dataset_dir / "costs_2040-modifications.csv"
            raw_file.write_text("technology,parameter,value\nOCGT,investment,696\n", encoding="utf-8")
            self.assertEqual(
                self.call_main(["scan-index", "raw_data/cost", "to", "user", "--workspace-root", str(workspace_root)])[0],
                0,
            )

            local_path = loom.get("user/cost/costs_2040-modifications.csv", workspace_root=workspace_root)

            self.assertEqual(local_path.read_text(encoding="utf-8"), raw_file.read_text(encoding="utf-8"))
            self.assertTrue(local_path.exists())

    def test_raw_snapshot_uses_recorded_scan_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            dataset_dir = workspace_root / "raw_data" / "cost"
            dataset_dir.mkdir(parents=True, exist_ok=True)
            (dataset_dir / "loom.md").write_text("source: https://example.com/cost\n\nCost dataset", encoding="utf-8")
            raw_file = dataset_dir / "costs_2040-modifications.csv"
            raw_file.write_text("technology,parameter,value\nOCGT,investment,696\n", encoding="utf-8")
            self.assertEqual(
                self.call_main(["scan-index", "raw_data/cost", "to", "user", "--workspace-root", str(workspace_root)])[0],
                0,
            )

            snapshot = build_raw_workspace_snapshot(workspace_root, "user")

            self.assertEqual({file.path for file in snapshot.files}, {"cost/loom.md", "cost/costs_2040-modifications.csv"})
            self.assertEqual(
                next(file.content for file in snapshot.files if file.path == "cost/costs_2040-modifications.csv"),
                raw_file.read_bytes(),
            )

    def test_push_records_dataset_prefixed_raw_paths_for_source_root_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_workspace = root / "source"
            app = create_app(f"sqlite:///{root / 'loom.db'}", root / "server-storage")
            dataset_dir = source_workspace / "technology-data"
            dataset_dir.mkdir(parents=True, exist_ok=True)
            (dataset_dir / "loom.md").write_text("source: https://example.com/cost\n\nCost dataset", encoding="utf-8")
            raw_file = dataset_dir / "costs_2040-modifications.csv"
            raw_file.write_text("technology,parameter,value\nOCGT,investment,696\n", encoding="utf-8")
            self.assertEqual(
                self.call_main(["scan-index", "technology-data", "to", "cost", "--workspace-root", str(source_workspace)])[0],
                0,
            )
            self.assertEqual(self.call_main(["confirm", "cost", "--workspace-root", str(source_workspace)])[0], 0)

            with TestClient(app) as client, self.patch_server(client):
                self.assertEqual(
                    self.call_main(["push", "cost", "--workspace-root", str(source_workspace), "--server-url", "http://loom.test"])[0],
                    0,
                )
                manifest = self.call_app(client, "GET", "http://loom.test/api/workspaces/cost/raw-manifest")

            self.assertIn("technology-data/loom.md", manifest["raw_manifest"])
            self.assertIn("technology-data/costs_2040-modifications.csv", manifest["raw_manifest"])

    def test_get_downloads_missing_remote_raw_file_and_reuses_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_workspace = root / "source"
            target_workspace = root / "target"
            app = create_app(f"sqlite:///{root / 'loom.db'}", root / "server-storage")
            self.write_energy_dataset(source_workspace)
            self.assertEqual(self.call_main([*self.scan_command(), "--workspace-root", str(source_workspace)])[0], 0)
            self.assertEqual(self.call_main(["confirm", "energy", "--workspace-root", str(source_workspace)])[0], 0)
            with TestClient(app) as client, self.patch_server(client):
                self.assertEqual(self.call_main(["push", "energy", "--workspace-root", str(source_workspace), "--server-url", "http://loom.test"])[0], 0)
                first = loom.get("energy/technology-data/costs.csv", workspace_root=target_workspace, server_url="http://loom.test")
                second = loom.get("energy/technology-data/costs.csv", workspace_root=target_workspace, server_url="http://loom.test")
                self.assertEqual(first, second)

    def test_pull_raw_command_downloads_workspace_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_workspace = root / "source"
            target_workspace = root / "target"
            app = create_app(f"sqlite:///{root / 'loom.db'}", root / "server-storage")
            self.write_energy_dataset(source_workspace)
            self.call_main([*self.scan_command(), "--workspace-root", str(source_workspace)])
            self.call_main(["confirm", "energy", "--workspace-root", str(source_workspace)])
            with TestClient(app) as client, self.patch_server(client):
                self.call_main(["push", "energy", "--workspace-root", str(source_workspace), "--server-url", "http://loom.test"])
                exit_code, output = self.call_main(["pull-raw", "energy", "--workspace-root", str(target_workspace), "--server-url", "http://loom.test"])
                self.assertEqual(exit_code, 0)
                self.assertIn("Pulled raw workspace: energy", output)

    def test_missing_raw_blob_is_reported_missing_and_can_be_restored(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_workspace = root / "source"
            storage_root = root / "server-storage"
            app = create_app(f"sqlite:///{root / 'loom.db'}", storage_root)
            raw_file = self.write_energy_dataset(source_workspace)
            self.call_main([*self.scan_command(), "--workspace-root", str(source_workspace)])
            self.call_main(["confirm", "energy", "--workspace-root", str(source_workspace)])
            with TestClient(app) as client, self.patch_server(client):
                self.call_main(["push", "energy", "--workspace-root", str(source_workspace), "--server-url", "http://loom.test"])
                raw_sha = sha256(raw_file.read_bytes()).hexdigest()
                missing_blob = raw_blob_storage_path(storage_root, raw_sha)
                self.assertTrue(missing_blob.exists())
                missing_blob.unlink()
                exists_payload = self.call_app(client, "POST", "http://loom.test/api/raw/exists", {"hashes": [raw_sha]})
                self.assertEqual(exists_payload["missing_hashes"], [raw_sha])
                content_base64 = base64.b64encode(raw_file.read_bytes()).decode("ascii")
                restore_payload = self.call_app(client, "POST", "http://loom.test/api/raw/objects", {"objects": [{"sha256": raw_sha, "size_bytes": raw_file.stat().st_size, "content_base64": content_base64}]})
                self.assertEqual(restore_payload["stored_count"], 1)
                self.assertTrue(missing_blob.exists())
