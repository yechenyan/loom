from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

import loom
from loom_server.sync_server import create_app

from .support import LoomTestCase


class RawAccessCacheTest(LoomTestCase):
    def test_get_links_existing_local_raw_file_without_remote_download(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            raw_file = self.write_energy_dataset(workspace_root)
            local_path = loom.get("energy/technology-data/costs.csv", workspace_root=workspace_root)
            self.assertEqual(local_path.read_text(encoding="utf-8"), raw_file.read_text(encoding="utf-8"))
            self.assertTrue(local_path.exists())

    def test_get_downloads_missing_remote_raw_file_and_reuses_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_workspace = root / "source"
            target_workspace = root / "target"
            app = create_app(f"sqlite:///{root / 'loom.db'}", root / "server-storage")
            self.write_energy_dataset(source_workspace)
            self.assertEqual(self.call_main(["scan", "energy", "--workspace-root", str(source_workspace)])[0], 0)
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
            self.call_main(["scan", "energy", "--workspace-root", str(source_workspace)])
            self.call_main(["confirm", "energy", "--workspace-root", str(source_workspace)])
            with TestClient(app) as client, self.patch_server(client):
                self.call_main(["push", "energy", "--workspace-root", str(source_workspace), "--server-url", "http://loom.test"])
                exit_code, output = self.call_main(["pull-raw", "energy", "--workspace-root", str(target_workspace), "--server-url", "http://loom.test"])
                self.assertEqual(exit_code, 0)
                self.assertIn("Pulled raw workspace: energy", output)
