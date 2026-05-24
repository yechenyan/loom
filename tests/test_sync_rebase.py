from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from loom_server.sync_server import create_app

from .support import LoomTestCase


class SyncRebaseTest(LoomTestCase):
    def test_push_auto_rebases_local_commits_before_sync(self) -> None:
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
                note = workspace_b / "loom" / "loom_explore" / "energy" / "notes" / "local.md"
                note.parent.mkdir(parents=True, exist_ok=True)
                note.write_text("local note\n", encoding="utf-8")
                self.call_main(["confirm", "energy", "--workspace-root", str(workspace_b)])
                self.write_energy_dataset(workspace_a, cost_value="42")
                self.call_main(["scan", "energy", "--workspace-root", str(workspace_a)])
                self.call_main(["confirm", "energy", "--workspace-root", str(workspace_a)])
                self.call_main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", "http://loom.test"])
                self.assertEqual(self.call_main(["push", "energy", "--workspace-root", str(workspace_b), "--server-url", "http://loom.test"])[0], 0)
                self.call_main(["pull", "energy", "--workspace-root", str(workspace_c), "--server-url", "http://loom.test"])
                self.assertEqual((workspace_c / "loom" / "loom_explore" / "energy" / "notes" / "local.md").read_text(encoding="utf-8"), "local note\n")

    def test_pull_rebases_local_commits_when_workspace_has_confirmed_changes(self) -> None:
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
                note = workspace_b / "loom" / "loom_explore" / "energy" / "notes" / "local.md"
                note.parent.mkdir(parents=True, exist_ok=True)
                note.write_text("local note from pull\n", encoding="utf-8")
                self.call_main(["confirm", "energy", "--workspace-root", str(workspace_b)])
                self.write_energy_dataset(workspace_a, cost_value="33")
                self.call_main(["scan", "energy", "--workspace-root", str(workspace_a)])
                self.call_main(["confirm", "energy", "--workspace-root", str(workspace_a)])
                self.call_main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", "http://loom.test"])
                self.assertIn("Changed: yes", self.call_main(["pull", "energy", "--workspace-root", str(workspace_b), "--server-url", "http://loom.test"])[1])
