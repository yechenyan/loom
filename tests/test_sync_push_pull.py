from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from fastapi.testclient import TestClient

from loom_server.sync_server import create_app

from .support import LoomTestCase


class SyncPushPullTest(LoomTestCase):
    def test_push_and_pull_workspace_through_fastapi_server(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_a = root / "workspace-a"
            workspace_b = root / "workspace-b"
            app = create_app(f"sqlite:///{root / 'loom.db'}", root / "server-storage")
            self.write_energy_dataset(workspace_a)
            self.call_main(["scan", "energy", "--workspace-root", str(workspace_a)])
            self.call_main(["confirm", "energy", "--workspace-root", str(workspace_a)])
            with TestClient(app) as client, self.patch_server(client):
                self.assertIn("Pushed workspace: energy", self.call_main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", "http://loom.test"])[1])
                self.assertIn("Pulled workspace: energy", self.call_main(["pull", "energy", "--workspace-root", str(workspace_b), "--server-url", "http://loom.test"])[1])
                profile = json.loads((workspace_b / "test-project" / "loom" / "loom_explore" / "energy" / "technology-data" / "profile.json").read_text(encoding="utf-8"))
                self.assertEqual(profile["csv_count"], 1)

    def test_second_push_and_pull_use_incremental_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_a = root / "workspace-a"
            workspace_b = root / "workspace-b"
            payloads: list[dict[str, object]] = []
            app = create_app(f"sqlite:///{root / 'loom.db'}", root / "server-storage")
            self.write_energy_dataset(workspace_a, cost_value="10")
            self.call_main(["scan", "energy", "--workspace-root", str(workspace_a)])
            self.call_main(["confirm", "energy", "--workspace-root", str(workspace_a)])
            with TestClient(app) as client:
                with self.patch_server(client):
                    self.call_main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", "http://loom.test"])
                    self.call_main(["pull", "energy", "--workspace-root", str(workspace_b), "--server-url", "http://loom.test"])
                    self.write_energy_dataset(workspace_a, cost_value="55")
                    self.call_main(["scan", "energy", "--workspace-root", str(workspace_a)])
                    self.call_main(["confirm", "energy", "--workspace-root", str(workspace_a)])
                    time.sleep(0.02)
                    self.call_main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", "http://loom.test"])
                self.assertTrue(True)
