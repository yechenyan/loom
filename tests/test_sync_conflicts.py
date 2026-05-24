from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from loom_server.sync_server import create_app

from .support import LoomTestCase


class SyncConflictTest(LoomTestCase):
    def test_pull_stops_on_conflict_and_waits_for_confirm(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_a = root / "workspace-a"
            workspace_b = root / "workspace-b"
            app = create_app(f"sqlite:///{root / 'loom.db'}", root / "server-storage")
            self.write_energy_dataset(workspace_a, cost_value="10")
            self.call_main(["scan", "energy", "--workspace-root", str(workspace_a)])
            self.call_main(["confirm", "energy", "--workspace-root", str(workspace_a)])
            with TestClient(app) as client, self.patch_server(client):
                self.call_main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", "http://loom.test"])
                self.call_main(["pull", "energy", "--workspace-root", str(workspace_b), "--server-url", "http://loom.test"])
                readme_a = workspace_a / "test-project" / "loom" / "loom_explore" / "energy" / "README.md"
                readme_b = workspace_b / "test-project" / "loom" / "loom_explore" / "energy" / "README.md"
                readme_a.write_text("remote pull conflict\n", encoding="utf-8")
                readme_b.write_text("local pull conflict\n", encoding="utf-8")
                self.call_main(["confirm", "energy", "--workspace-root", str(workspace_a)])
                self.call_main(["confirm", "energy", "--workspace-root", str(workspace_b)])
                self.call_main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", "http://loom.test"])
                exit_code, output = self.call_main(["pull", "energy", "--workspace-root", str(workspace_b), "--server-url", "http://loom.test"])
                self.assertEqual(exit_code, 1)
                self.assertIn("Conflict detected during rebase", output)

    def test_push_stops_on_conflict_then_allows_confirm_and_push(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_a = root / "workspace-a"
            workspace_b = root / "workspace-b"
            workspace_c = root / "workspace-c"
            app = create_app(f"sqlite:///{root / 'loom.db'}", root / "server-storage")
            self.write_energy_dataset(workspace_a, cost_value="10")
            self.call_main(["scan", "energy", "--workspace-root", str(workspace_a)])
            self.call_main(["confirm", "energy", "--workspace-root", str(workspace_a)])
            with TestClient(app) as client, self.patch_server(client):
                self.call_main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", "http://loom.test"])
                self.call_main(["pull", "energy", "--workspace-root", str(workspace_b), "--server-url", "http://loom.test"])
                readme_a = workspace_a / "test-project" / "loom" / "loom_explore" / "energy" / "README.md"
                readme_b = workspace_b / "test-project" / "loom" / "loom_explore" / "energy" / "README.md"
                readme_a.write_text("remote change\n", encoding="utf-8")
                readme_b.write_text("local change\n", encoding="utf-8")
                self.call_main(["confirm", "energy", "--workspace-root", str(workspace_a)])
                self.call_main(["confirm", "energy", "--workspace-root", str(workspace_b)])
                self.call_main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", "http://loom.test"])
                self.assertEqual(self.call_main(["push", "energy", "--workspace-root", str(workspace_b), "--server-url", "http://loom.test"])[0], 1)
                readme_b.write_text("resolved change\n", encoding="utf-8")
                self.call_main(["confirm", "energy", "--workspace-root", str(workspace_b)])
                self.call_main(["push", "energy", "--workspace-root", str(workspace_b), "--server-url", "http://loom.test"])
                self.call_main(["pull", "energy", "--workspace-root", str(workspace_c), "--server-url", "http://loom.test"])
                self.assertEqual((workspace_c / "test-project" / "loom" / "loom_explore" / "energy" / "README.md").read_text(encoding="utf-8"), "resolved change\n")
