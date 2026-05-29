from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

import loom
from loom_server.sync_server import create_app

from .support import LoomTestCase


class RawAccessRefreshTest(LoomTestCase):
    def test_pull_api_refreshes_changed_and_deleted_raw_files_incrementally(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_workspace = root / "source"
            target_workspace = root / "target"
            app = create_app(f"sqlite:///{root / 'loom.db'}", root / "server-storage")
            self.write_energy_dataset(source_workspace, cost_value="10", include_legacy_file=True)
            self.call_main([*self.scan_command(), "--workspace-root", str(source_workspace)])
            self.call_main(["confirm", "energy", "--workspace-root", str(source_workspace)])
            with TestClient(app) as client, self.patch_server(client):
                self.call_main(["push", "energy", "--workspace-root", str(source_workspace), "--server-url", "http://loom.test"])
                first_pull = loom.pull("energy", workspace_root=target_workspace, server_url="http://loom.test")
                self.assertEqual(first_pull[0].downloaded_file_count, 3)
                self.write_energy_dataset(source_workspace, cost_value="25", include_legacy_file=False)
                self.call_main(["push", "energy", "--workspace-root", str(source_workspace), "--server-url", "http://loom.test"])
                second_pull = loom.pull("energy", workspace_root=target_workspace, server_url="http://loom.test")
                self.assertEqual(second_pull[0].downloaded_file_count, 1)
                self.assertEqual(second_pull[0].deleted_file_count, 1)

    def test_pull_only_refreshes_cached_raw_files_and_writes_conflict_notice(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_workspace = root / "source"
            target_workspace = root / "target"
            app = create_app(f"sqlite:///{root / 'loom.db'}", root / "server-storage")
            self.write_energy_dataset(source_workspace, cost_value="10", include_legacy_file=True)
            self.call_main([*self.scan_command(), "--workspace-root", str(source_workspace)])
            self.call_main(["confirm", "energy", "--workspace-root", str(source_workspace)])
            with TestClient(app) as client, self.patch_server(client):
                self.call_main(["push", "energy", "--workspace-root", str(source_workspace), "--server-url", "http://loom.test"])
                self.call_main(["pull", "energy", "--workspace-root", str(target_workspace), "--server-url", "http://loom.test"])
                cached_costs = loom.get("energy/technology-data/costs.csv", workspace_root=target_workspace, server_url="http://loom.test")
                local_raw_costs = target_workspace / "raw_data" / "energy" / "technology-data" / "costs.csv"
                local_raw_costs.parent.mkdir(parents=True, exist_ok=True)
                (local_raw_costs.parent / "loom.md").write_text("Energy dataset", encoding="utf-8")
                local_raw_costs.write_text("tech,cost\nsolar,999\n", encoding="utf-8")
                self.write_energy_dataset(source_workspace, cost_value="25", include_legacy_file=True)
                self.call_main([*self.scan_command(), "--workspace-root", str(source_workspace)])
                self.call_main(["confirm", "energy", "--workspace-root", str(source_workspace)])
                self.call_main(["push", "energy", "--workspace-root", str(source_workspace), "--server-url", "http://loom.test"])
                exit_code, output = self.call_main(["pull", "energy", "--workspace-root", str(target_workspace), "--server-url", "http://loom.test"])
                self.assertEqual(exit_code, 0)
                self.assertIn("Raw conflict notice:", output)
                self.assertIn("solar,25", cached_costs.read_text(encoding="utf-8"))
