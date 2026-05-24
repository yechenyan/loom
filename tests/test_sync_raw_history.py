from __future__ import annotations

import tempfile
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

import loom.sync_client as sync_client
from loom_server.sync_server import create_app
from loom_server.sync_service import raw_objects_table, workspace_raw_current_table, workspace_raw_history_table

from .support import LoomTestCase


class SyncRawHistoryTest(LoomTestCase):
    def test_push_uploads_raw_objects_incrementally_and_tracks_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace-a"
            duplicate_dir = workspace / "test-project" / "loom" / "loom_raw" / "energy" / "copies"
            app = create_app(f"sqlite:///{root / 'loom.db'}", root / "server-storage")
            self.write_energy_dataset(workspace, cost_value="10")
            duplicate_dir.mkdir(parents=True, exist_ok=True)
            source = workspace / "test-project" / "loom" / "loom_raw" / "energy" / "technology-data" / "costs.csv"
            (duplicate_dir / "costs-copy.csv").write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            self.call_main(["scan", "energy", "--workspace-root", str(workspace)])
            self.call_main(["confirm", "energy", "--workspace-root", str(workspace)])
            request_log: list[tuple[str, str, dict[str, object] | None]] = []
            with TestClient(app) as client:
                with mock.patch.object(sync_client, "_request_json", side_effect=lambda method, url, payload=None: request_log.append((method, url, payload)) or self.call_app(client, method, url, payload)):
                    self.call_main(["push", "energy", "--workspace-root", str(workspace), "--server-url", "http://loom.test"])
                service = client.app.state.sync_service
                with service.engine.begin() as connection:
                    self.assertEqual(len(list(connection.execute(raw_objects_table.select()).mappings())), 2)
                    self.assertEqual(len(list(connection.execute(workspace_raw_current_table.select()).mappings())), 3)
                    self.assertEqual(len(list(connection.execute(workspace_raw_history_table.select()).mappings())), 3)
