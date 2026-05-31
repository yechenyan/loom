from __future__ import annotations

import shutil
import json
import sys
from pathlib import Path
import tempfile
import textwrap
import unittest

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom-server" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

from loom.scanner import scan_topic_to_explore
from loom.workspace_snapshot import build_workspace_snapshot, encode_workspace_files
from loom_server.sync_server import create_app


class ExploreApiTest(unittest.TestCase):
    def test_lists_explore_workspace_and_dataset_profiles_from_synced_revision(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            dataset_dir = workspace_root / "raw_data" / "energy" / "technology-data"
            dataset_dir.mkdir(parents=True)
            (dataset_dir / "loom.md").write_text(
                "source: https://example.com/energy\n\nEnergy dataset",
                encoding="utf-8",
            )
            (dataset_dir / "costs.csv").write_text(
                textwrap.dedent(
                    """\
                    tech,cost
                    solar,10
                    wind,20
                    """
                ),
                encoding="utf-8",
            )

            scan_topic_to_explore("energy", workspace_root)
            snapshot = build_workspace_snapshot(workspace_root, "energy")
            app = create_app(f"sqlite:///{workspace_root / 'loom.db'}", workspace_root / ".loom-server-storage")

            with TestClient(app) as client:
                push_response = client.post(
                    "/api/workspaces/energy/push",
                    json={
                        "base_revision": None,
                        "local_commit": None,
                        "tree_hash": snapshot.tree_hash,
                        "message": "Push workspace energy",
                        "files": encode_workspace_files(snapshot.files),
                        "deleted_paths": [],
                        "raw_files": [],
                        "raw_deleted_paths": [],
                    },
                )
                self.assertEqual(push_response.status_code, 200)
                shutil.rmtree(workspace_root / "loom")

                response = client.get("/api/explore/workspaces")
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertEqual(payload["workspaces"][0]["name"], "energy")
                self.assertEqual(payload["workspaces"][0]["dataset_count"], 1)

                workspace_response = client.get("/api/explore/workspaces/energy")
                self.assertEqual(workspace_response.status_code, 200)
                workspace_payload = workspace_response.json()
                self.assertEqual(workspace_payload["name"], "energy")
                self.assertEqual(workspace_payload["datasets"][0]["name"], "technology-data")
                self.assertEqual(workspace_payload["datasets"][0]["csv_profiles"][0]["row_count"], 2)


if __name__ == "__main__":
    unittest.main()
