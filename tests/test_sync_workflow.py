from __future__ import annotations

import io
import json
import sys
from pathlib import Path
import tempfile
import textwrap
import time
import unittest
from contextlib import redirect_stdout
from unittest import mock

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

from loom.cli import main
import loom.sync_client as sync_client
from loom.sync_server import create_app
from loom.sync_service import raw_objects_table, workspace_raw_current_table, workspace_raw_history_table


class SyncWorkflowTest(unittest.TestCase):
    def test_push_and_pull_workspace_through_fastapi_server(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_a = root / "workspace-a"
            workspace_b = root / "workspace-b"
            database_path = root / "loom.db"
            storage_root = root / "server-storage"

            self._write_energy_dataset(workspace_a)

            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", "energy", "--workspace-root", str(workspace_a)]), 0)
                self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_a)]), 0)

            app = create_app(f"sqlite:///{database_path}", storage_root)
            with TestClient(app) as client:
                server_url = "http://loom.test"
                with mock.patch.object(
                    sync_client,
                    "_request_json",
                    side_effect=lambda method, url, payload=None: self._call_app(client, method, url, payload),
                ):
                    push_stdout = io.StringIO()
                    with redirect_stdout(push_stdout):
                        exit_code = main(
                            [
                                "push",
                                "energy",
                                "--workspace-root",
                                str(workspace_a),
                                "--server-url",
                                server_url,
                            ]
                        )
                    self.assertEqual(exit_code, 0)
                    self.assertIn("Pushed workspace: energy", push_stdout.getvalue())
                    self.assertIn("Changed files:", push_stdout.getvalue())
                    self.assertIn("Raw objects uploaded:", push_stdout.getvalue())

                    pull_stdout = io.StringIO()
                    with redirect_stdout(pull_stdout):
                        exit_code = main(
                            [
                                "pull",
                                "energy",
                                "--workspace-root",
                                str(workspace_b),
                                "--server-url",
                                server_url,
                            ]
                        )
                    self.assertEqual(exit_code, 0)
                    self.assertIn("Pulled workspace: energy", pull_stdout.getvalue())
                    self.assertIn("Changed files:", pull_stdout.getvalue())

                    profile_path = (
                        workspace_b
                        / "test-project"
                        / "loom"
                        / "loom_explore"
                        / "energy"
                        / "technology-data"
                        / "profile.json"
                    )
                    self.assertTrue(profile_path.exists())
                    profile = json.loads(profile_path.read_text(encoding="utf-8"))
                    self.assertEqual(profile["csv_count"], 1)

                    status_stdout = io.StringIO()
                    with redirect_stdout(status_stdout):
                        exit_code = main(["status", "energy", "--workspace-root", str(workspace_b)])
                    self.assertEqual(exit_code, 0)
                    self.assertIn("No pending changes.", status_stdout.getvalue())

    def test_pull_overwrites_local_workspace_and_push_auto_confirms(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_a = root / "workspace-a"
            workspace_b = root / "workspace-b"
            database_path = root / "loom.db"
            storage_root = root / "server-storage"

            self._write_energy_dataset(workspace_a, cost_value="10")
            self._write_energy_dataset(workspace_b, cost_value="999")

            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", "energy", "--workspace-root", str(workspace_a)]), 0)
                self.assertEqual(main(["scan", "energy", "--workspace-root", str(workspace_b)]), 0)
                self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_b)]), 0)

            app = create_app(f"sqlite:///{database_path}", storage_root)
            with TestClient(app) as client:
                server_url = "http://loom.test"
                with mock.patch.object(
                    sync_client,
                    "_request_json",
                    side_effect=lambda method, url, payload=None: self._call_app(client, method, url, payload),
                ):
                    push_stdout = io.StringIO()
                    with redirect_stdout(push_stdout):
                        exit_code = main(
                            [
                                "push",
                                "energy",
                                "--workspace-root",
                                str(workspace_a),
                                "--server-url",
                                server_url,
                            ]
                        )
                    self.assertEqual(exit_code, 0)
                    self.assertIn("Pushed workspace: energy", push_stdout.getvalue())

                    local_profile_before = (
                        workspace_b
                        / "test-project"
                        / "loom"
                        / "loom_explore"
                        / "energy"
                        / "technology-data"
                        / "profile.json"
                    )
                    self.assertTrue(local_profile_before.exists())

                    pull_stdout = io.StringIO()
                    with redirect_stdout(pull_stdout):
                        exit_code = main(
                            [
                                "pull",
                                "energy",
                                "--workspace-root",
                                str(workspace_b),
                                "--server-url",
                                server_url,
                            ]
                        )
                    self.assertEqual(exit_code, 0)
                    self.assertIn("Changed: yes", pull_stdout.getvalue())

                    remote_profile = (
                        workspace_a
                        / "test-project"
                        / "loom"
                        / "loom_explore"
                        / "energy"
                        / "technology-data"
                        / "profile.json"
                    )
                    self.assertEqual(
                        local_profile_before.read_text(encoding="utf-8"),
                        remote_profile.read_text(encoding="utf-8"),
                    )

    def test_second_push_and_pull_use_incremental_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_a = root / "workspace-a"
            workspace_b = root / "workspace-b"
            database_path = root / "loom.db"
            storage_root = root / "server-storage"
            payloads: list[dict[str, object]] = []

            self._write_energy_dataset(workspace_a, cost_value="10")

            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", "energy", "--workspace-root", str(workspace_a)]), 0)
                self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_a)]), 0)

            app = create_app(f"sqlite:///{database_path}", storage_root)
            with TestClient(app) as client:
                server_url = "http://loom.test"

                def capture_request(method: str, url: str, payload: dict[str, object] | None = None) -> dict[str, object]:
                    if payload is not None:
                        payloads.append(payload)
                    return self._call_app(client, method, url, payload)

                with mock.patch.object(sync_client, "_request_json", side_effect=capture_request):
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(
                            main(
                                [
                                    "push",
                                    "energy",
                                    "--workspace-root",
                                    str(workspace_a),
                                    "--server-url",
                                    server_url,
                                ]
                            ),
                            0,
                        )
                        self.assertEqual(
                            main(
                                [
                                    "pull",
                                    "energy",
                                    "--workspace-root",
                                    str(workspace_b),
                                    "--server-url",
                                    server_url,
                                ]
                            ),
                            0,
                        )

                    self._write_energy_dataset(workspace_a, cost_value="55")
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(main(["scan", "energy", "--workspace-root", str(workspace_a)]), 0)
                        self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_a)]), 0)

                    beta_profile = (
                        workspace_b
                        / "test-project"
                        / "loom"
                        / "loom_explore"
                        / "energy"
                        / "technology-data"
                        / "profile.json"
                    )
                    beta_profile_before_mtime = beta_profile.stat().st_mtime_ns
                    readme_path = (
                        workspace_b
                        / "test-project"
                        / "loom"
                        / "loom_explore"
                        / "energy"
                        / "README.md"
                    )
                    readme_before_mtime = readme_path.stat().st_mtime_ns

                    time.sleep(0.02)
                    push_stdout = io.StringIO()
                    with redirect_stdout(push_stdout):
                        self.assertEqual(
                            main(
                                [
                                    "push",
                                    "energy",
                                    "--workspace-root",
                                    str(workspace_a),
                                    "--server-url",
                                    server_url,
                                ]
                            ),
                            0,
                        )
                    push_payloads = [payload for payload in payloads if isinstance(payload, dict) and "tree_hash" in payload]
                    first_push_payload = push_payloads[0]
                    second_push_payload = push_payloads[-1]
                    changed_paths = sorted(str(item["path"]) for item in second_push_payload["files"])
                    self.assertTrue(changed_paths)
                    self.assertLess(len(changed_paths), len(first_push_payload["files"]))
                    self.assertNotIn("README.md", changed_paths)
                    self.assertEqual(second_push_payload["deleted_paths"], [])
                    self.assertIn("Changed files:", push_stdout.getvalue())

                    pull_stdout = io.StringIO()
                    with redirect_stdout(pull_stdout):
                        self.assertEqual(
                            main(
                                [
                                    "pull",
                                    "energy",
                                    "--workspace-root",
                                    str(workspace_b),
                                    "--server-url",
                                    server_url,
                                ]
                            ),
                            0,
                        )
                    self.assertIn("Changed: yes", pull_stdout.getvalue())
                    self.assertIn("Deleted files: 0", pull_stdout.getvalue())
                    self.assertGreater(beta_profile.stat().st_mtime_ns, beta_profile_before_mtime)
                    self.assertEqual(readme_path.stat().st_mtime_ns, readme_before_mtime)

    def test_push_uploads_raw_objects_incrementally_and_tracks_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace = root / "workspace-a"
            database_path = root / "loom.db"
            storage_root = root / "server-storage"
            request_log: list[tuple[str, str, dict[str, object] | None]] = []

            self._write_energy_dataset(workspace, cost_value="10")
            duplicate_dir = workspace / "test-project" / "loom" / "loom_raw" / "energy" / "copies"
            duplicate_dir.mkdir(parents=True, exist_ok=True)
            same_content = (workspace / "test-project" / "loom" / "loom_raw" / "energy" / "technology-data" / "costs.csv").read_text(encoding="utf-8")
            (duplicate_dir / "costs-copy.csv").write_text(same_content, encoding="utf-8")

            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", "energy", "--workspace-root", str(workspace)]), 0)
                self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace)]), 0)

            app = create_app(f"sqlite:///{database_path}", storage_root)
            with TestClient(app) as client:
                server_url = "http://loom.test"

                def capture_request(method: str, url: str, payload: dict[str, object] | None = None) -> dict[str, object]:
                    request_log.append((method, url, payload))
                    return self._call_app(client, method, url, payload)

                with mock.patch.object(sync_client, "_request_json", side_effect=capture_request):
                    push_stdout = io.StringIO()
                    with redirect_stdout(push_stdout):
                        self.assertEqual(
                            main(
                                [
                                    "push",
                                    "energy",
                                    "--workspace-root",
                                    str(workspace),
                                    "--server-url",
                                    server_url,
                                ]
                            ),
                            0,
                        )
                    self.assertIn("Raw objects uploaded:", push_stdout.getvalue())

                    raw_exists_calls = [entry for entry in request_log if entry[1].endswith("/api/raw/exists")]
                    raw_upload_calls = [entry for entry in request_log if entry[1].endswith("/api/raw/objects")]
                    self.assertEqual(len(raw_exists_calls), 1)
                    self.assertEqual(len(raw_upload_calls), 1)
                    uploaded_objects = list(raw_upload_calls[0][2]["objects"])
                    self.assertEqual(len(uploaded_objects), 2)

                    service = client.app.state.sync_service
                    with service.engine.begin() as connection:
                        raw_object_rows = list(connection.execute(raw_objects_table.select()).mappings())
                        current_rows = list(
                            connection.execute(
                                workspace_raw_current_table.select().order_by(workspace_raw_current_table.c.path)
                            ).mappings()
                        )
                        history_rows = list(
                            connection.execute(
                                workspace_raw_history_table.select().order_by(workspace_raw_history_table.c.id)
                            ).mappings()
                        )
                    self.assertEqual(len(raw_object_rows), 2)
                    self.assertEqual(len(current_rows), 3)
                    self.assertEqual(len(history_rows), 3)

                    request_log.clear()
                    original_copy = duplicate_dir / "costs-copy.csv"
                    renamed_copy = duplicate_dir / "renamed-costs.csv"
                    original_copy.rename(renamed_copy)

                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(main(["scan", "energy", "--workspace-root", str(workspace)]), 0)
                        self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace)]), 0)
                        self.assertEqual(
                            main(
                                [
                                    "push",
                                    "energy",
                                    "--workspace-root",
                                    str(workspace),
                                    "--server-url",
                                    server_url,
                                ]
                            ),
                            0,
                        )

                    raw_upload_calls = [entry for entry in request_log if entry[1].endswith("/api/raw/objects")]
                    self.assertEqual(raw_upload_calls, [])

                    with service.engine.begin() as connection:
                        current_rows = list(
                            connection.execute(
                                workspace_raw_current_table.select().order_by(workspace_raw_current_table.c.path)
                            ).mappings()
                        )
                        history_rows = list(
                            connection.execute(
                                workspace_raw_history_table.select().order_by(workspace_raw_history_table.c.id)
                            ).mappings()
                        )
                    current_paths = [str(row["path"]) for row in current_rows]
                    self.assertIn("copies/renamed-costs.csv", current_paths)
                    self.assertNotIn("copies/costs-copy.csv", current_paths)
                    history_actions = [(str(row["path"]), str(row["action"])) for row in history_rows]
                    self.assertIn(("copies/costs-copy.csv", "deleted"), history_actions)
                    self.assertIn(("copies/renamed-costs.csv", "created"), history_actions)

    def test_push_auto_rebases_local_commits_before_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_a = root / "workspace-a"
            workspace_b = root / "workspace-b"
            workspace_c = root / "workspace-c"
            database_path = root / "loom.db"
            storage_root = root / "server-storage"

            self._write_energy_dataset(workspace_a, cost_value="10")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", "energy", "--workspace-root", str(workspace_a)]), 0)
                self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_a)]), 0)

            app = create_app(f"sqlite:///{database_path}", storage_root)
            with TestClient(app) as client:
                server_url = "http://loom.test"
                with mock.patch.object(
                    sync_client,
                    "_request_json",
                    side_effect=lambda method, url, payload=None: self._call_app(client, method, url, payload),
                ):
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(
                            main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", server_url]),
                            0,
                        )
                        self.assertEqual(
                            main(["pull", "energy", "--workspace-root", str(workspace_b), "--server-url", server_url]),
                            0,
                        )

                    local_note = (
                        workspace_b / "test-project" / "loom" / "loom_explore" / "energy" / "notes" / "local.md"
                    )
                    local_note.parent.mkdir(parents=True, exist_ok=True)
                    local_note.write_text("local note\n", encoding="utf-8")
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_b)]), 0)

                    self._write_energy_dataset(workspace_a, cost_value="42")
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(main(["scan", "energy", "--workspace-root", str(workspace_a)]), 0)
                        self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_a)]), 0)
                        self.assertEqual(
                            main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", server_url]),
                            0,
                        )

                    push_stdout = io.StringIO()
                    with redirect_stdout(push_stdout):
                        self.assertEqual(
                            main(["push", "energy", "--workspace-root", str(workspace_b), "--server-url", server_url]),
                            0,
                        )
                    self.assertIn("Pushed workspace: energy", push_stdout.getvalue())

                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(
                            main(["pull", "energy", "--workspace-root", str(workspace_c), "--server-url", server_url]),
                            0,
                        )

                    remote_note = (
                        workspace_c / "test-project" / "loom" / "loom_explore" / "energy" / "notes" / "local.md"
                    )
                    remote_profile = (
                        workspace_c
                        / "test-project"
                        / "loom"
                        / "loom_explore"
                        / "energy"
                        / "technology-data"
                        / "profile.json"
                    )
                    self.assertEqual(remote_note.read_text(encoding="utf-8"), "local note\n")
                    self.assertIn('"csv_count": 1', remote_profile.read_text(encoding="utf-8"))

    def test_pull_rebases_local_commits_when_workspace_has_confirmed_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_a = root / "workspace-a"
            workspace_b = root / "workspace-b"
            database_path = root / "loom.db"
            storage_root = root / "server-storage"

            self._write_energy_dataset(workspace_a, cost_value="10")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", "energy", "--workspace-root", str(workspace_a)]), 0)
                self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_a)]), 0)

            app = create_app(f"sqlite:///{database_path}", storage_root)
            with TestClient(app) as client:
                server_url = "http://loom.test"
                with mock.patch.object(
                    sync_client,
                    "_request_json",
                    side_effect=lambda method, url, payload=None: self._call_app(client, method, url, payload),
                ):
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(
                            main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", server_url]),
                            0,
                        )
                        self.assertEqual(
                            main(["pull", "energy", "--workspace-root", str(workspace_b), "--server-url", server_url]),
                            0,
                        )

                    local_note = (
                        workspace_b / "test-project" / "loom" / "loom_explore" / "energy" / "notes" / "local.md"
                    )
                    local_note.parent.mkdir(parents=True, exist_ok=True)
                    local_note.write_text("local note from pull\n", encoding="utf-8")
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_b)]), 0)

                    self._write_energy_dataset(workspace_a, cost_value="33")
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(main(["scan", "energy", "--workspace-root", str(workspace_a)]), 0)
                        self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_a)]), 0)
                        self.assertEqual(
                            main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", server_url]),
                            0,
                        )

                    pull_stdout = io.StringIO()
                    with redirect_stdout(pull_stdout):
                        self.assertEqual(
                            main(["pull", "energy", "--workspace-root", str(workspace_b), "--server-url", server_url]),
                            0,
                        )
                    self.assertIn("Pulled workspace: energy", pull_stdout.getvalue())
                    self.assertIn("Changed: yes", pull_stdout.getvalue())

                    rebased_note = (
                        workspace_b / "test-project" / "loom" / "loom_explore" / "energy" / "notes" / "local.md"
                    )
                    rebased_profile = (
                        workspace_b
                        / "test-project"
                        / "loom"
                        / "loom_explore"
                        / "energy"
                        / "technology-data"
                        / "profile.json"
                    )
                    self.assertEqual(rebased_note.read_text(encoding="utf-8"), "local note from pull\n")
                    self.assertIn('"csv_count": 1', rebased_profile.read_text(encoding="utf-8"))

                    status_stdout = io.StringIO()
                    with redirect_stdout(status_stdout):
                        self.assertEqual(main(["status", "energy", "--workspace-root", str(workspace_b)]), 0)
                    self.assertIn("No pending changes.", status_stdout.getvalue())
                    self.assertIn("Pending rebase revision:", status_stdout.getvalue())

    def test_pull_stops_on_conflict_and_waits_for_confirm(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_a = root / "workspace-a"
            workspace_b = root / "workspace-b"
            database_path = root / "loom.db"
            storage_root = root / "server-storage"

            self._write_energy_dataset(workspace_a, cost_value="10")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", "energy", "--workspace-root", str(workspace_a)]), 0)
                self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_a)]), 0)

            app = create_app(f"sqlite:///{database_path}", storage_root)
            with TestClient(app) as client:
                server_url = "http://loom.test"
                with mock.patch.object(
                    sync_client,
                    "_request_json",
                    side_effect=lambda method, url, payload=None: self._call_app(client, method, url, payload),
                ):
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(
                            main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", server_url]),
                            0,
                        )
                        self.assertEqual(
                            main(["pull", "energy", "--workspace-root", str(workspace_b), "--server-url", server_url]),
                            0,
                        )

                    readme_a = workspace_a / "test-project" / "loom" / "loom_explore" / "energy" / "README.md"
                    readme_b = workspace_b / "test-project" / "loom" / "loom_explore" / "energy" / "README.md"
                    readme_a.write_text("remote pull conflict\n", encoding="utf-8")
                    readme_b.write_text("local pull conflict\n", encoding="utf-8")

                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_a)]), 0)
                        self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_b)]), 0)
                        self.assertEqual(
                            main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", server_url]),
                            0,
                        )

                    pull_stdout = io.StringIO()
                    with redirect_stdout(pull_stdout):
                        self.assertEqual(
                            main(["pull", "energy", "--workspace-root", str(workspace_b), "--server-url", server_url]),
                            1,
                        )
                    self.assertIn("Conflict detected during rebase", pull_stdout.getvalue())
                    self.assertIn("loom confirm energy", pull_stdout.getvalue())
                    self.assertIn("<<<<<<< LOCAL:README.md", readme_b.read_text(encoding="utf-8"))

                    status_stdout = io.StringIO()
                    with redirect_stdout(status_stdout):
                        self.assertEqual(main(["status", "energy", "--workspace-root", str(workspace_b)]), 0)
                    self.assertIn("Pending rebase revision:", status_stdout.getvalue())

    def test_push_stops_on_conflict_then_allows_confirm_and_push(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workspace_a = root / "workspace-a"
            workspace_b = root / "workspace-b"
            workspace_c = root / "workspace-c"
            database_path = root / "loom.db"
            storage_root = root / "server-storage"

            self._write_energy_dataset(workspace_a, cost_value="10")
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", "energy", "--workspace-root", str(workspace_a)]), 0)
                self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_a)]), 0)

            app = create_app(f"sqlite:///{database_path}", storage_root)
            with TestClient(app) as client:
                server_url = "http://loom.test"
                with mock.patch.object(
                    sync_client,
                    "_request_json",
                    side_effect=lambda method, url, payload=None: self._call_app(client, method, url, payload),
                ):
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(
                            main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", server_url]),
                            0,
                        )
                        self.assertEqual(
                            main(["pull", "energy", "--workspace-root", str(workspace_b), "--server-url", server_url]),
                            0,
                        )

                    readme_a = workspace_a / "test-project" / "loom" / "loom_explore" / "energy" / "README.md"
                    readme_b = workspace_b / "test-project" / "loom" / "loom_explore" / "energy" / "README.md"
                    readme_a.write_text("remote change\n", encoding="utf-8")
                    readme_b.write_text("local change\n", encoding="utf-8")

                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_a)]), 0)
                        self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_b)]), 0)
                        self.assertEqual(
                            main(["push", "energy", "--workspace-root", str(workspace_a), "--server-url", server_url]),
                            0,
                        )

                    push_stdout = io.StringIO()
                    with redirect_stdout(push_stdout):
                        self.assertEqual(
                            main(["push", "energy", "--workspace-root", str(workspace_b), "--server-url", server_url]),
                            1,
                        )
                    self.assertIn("Conflict detected during rebase", push_stdout.getvalue())
                    self.assertIn("<<<<<<< LOCAL:README.md", readme_b.read_text(encoding="utf-8"))

                    readme_b.write_text("resolved change\n", encoding="utf-8")
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace_b)]), 0)
                    final_push_stdout = io.StringIO()
                    with redirect_stdout(final_push_stdout):
                        self.assertEqual(
                            main(["push", "energy", "--workspace-root", str(workspace_b), "--server-url", server_url]),
                            0,
                        )
                    self.assertIn("Pushed workspace: energy", final_push_stdout.getvalue())

                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(
                            main(["pull", "energy", "--workspace-root", str(workspace_c), "--server-url", server_url]),
                            0,
                        )
                    readme_c = workspace_c / "test-project" / "loom" / "loom_explore" / "energy" / "README.md"
                    self.assertEqual(readme_c.read_text(encoding="utf-8"), "resolved change\n")

    def _write_energy_dataset(self, workspace_root: Path, cost_value: str = "10") -> None:
        dataset_dir = workspace_root / "test-project" / "loom" / "loom_raw" / "energy" / "technology-data"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        (dataset_dir / "loom.md").write_text(
            "source: https://example.com/energy\n\nEnergy dataset",
            encoding="utf-8",
        )
        (dataset_dir / "costs.csv").write_text(
            textwrap.dedent(
                """\
                tech,cost
                solar,{cost_value}
                wind,20
                """
            ).format(cost_value=cost_value),
            encoding="utf-8",
        )

    def _call_app(self, client: TestClient, method: str, url: str, payload: dict[str, object] | None = None) -> dict[str, object]:
        response = client.request(method, url, json=payload)
        if response.status_code >= 400:
            raise RuntimeError(f"Server request failed ({response.status_code}): {response.text}")
        return dict(response.json())


if __name__ == "__main__":
    unittest.main()
