from __future__ import annotations

import io
import sys
from pathlib import Path
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout
from unittest import mock

from fastapi.testclient import TestClient


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

import loom
from loom.cli import main
import loom.sync_client as sync_client
from loom.sync_server import create_app


class RawAccessTest(unittest.TestCase):
    def test_get_links_existing_local_raw_file_without_remote_download(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace_root = Path(temp_dir)
            raw_file = self._write_energy_dataset(workspace_root)

            local_path = loom.get("energy/technology-data/costs.csv", workspace_root=workspace_root)

            self.assertEqual(local_path.read_text(encoding="utf-8"), raw_file.read_text(encoding="utf-8"))
            self.assertEqual(
                local_path.resolve(),
                (
                    workspace_root
                    / "test-project"
                    / "loom"
                    / ".loom"
                    / "raw"
                    / "energy"
                    / "technology-data"
                    / "costs.csv"
                ).resolve(),
            )
            self.assertTrue(local_path.exists())

    def test_get_downloads_missing_remote_raw_file_and_reuses_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_workspace = root / "source"
            target_workspace = root / "target"
            database_path = root / "loom.db"
            storage_root = root / "server-storage"
            request_log: list[tuple[str, str]] = []

            self._write_energy_dataset(source_workspace)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", "energy", "--workspace-root", str(source_workspace)]), 0)
                self.assertEqual(main(["confirm", "energy", "--workspace-root", str(source_workspace)]), 0)

            app = create_app(f"sqlite:///{database_path}", storage_root)
            with TestClient(app) as client:
                server_url = "http://loom.test"

                def capture_request(method: str, url: str, payload=None):
                    request_log.append((method, url))
                    return self._call_app(client, method, url, payload)

                with mock.patch.object(sync_client, "_request_json", side_effect=capture_request):
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(
                            main(
                                [
                                    "push",
                                    "energy",
                                    "--workspace-root",
                                    str(source_workspace),
                                    "--server-url",
                                    server_url,
                                ]
                            ),
                            0,
                        )

                    local_path = loom.get(
                        "energy/technology-data/costs.csv",
                        workspace_root=target_workspace,
                        server_url=server_url,
                    )
                    self.assertTrue(local_path.exists())
                    self.assertIn("/api/workspaces/energy/raw-manifest", request_log[-2][1])
                    self.assertIn("/api/raw/objects/", request_log[-1][1])

                    call_count_after_first_get = len(request_log)
                    second_path = loom.get(
                        "energy/technology-data/costs.csv",
                        workspace_root=target_workspace,
                        server_url=server_url,
                    )
                    self.assertEqual(second_path, local_path)
                    self.assertEqual(len(request_log), call_count_after_first_get)

    def test_pull_raw_command_downloads_workspace_cache(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_workspace = root / "source"
            target_workspace = root / "target"
            database_path = root / "loom.db"
            storage_root = root / "server-storage"

            self._write_energy_dataset(source_workspace)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", "energy", "--workspace-root", str(source_workspace)]), 0)
                self.assertEqual(main(["confirm", "energy", "--workspace-root", str(source_workspace)]), 0)

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
                            main(
                                [
                                    "push",
                                    "energy",
                                    "--workspace-root",
                                    str(source_workspace),
                                    "--server-url",
                                    server_url,
                                ]
                            ),
                            0,
                        )

                    pull_stdout = io.StringIO()
                    with redirect_stdout(pull_stdout):
                        self.assertEqual(
                            main(
                                [
                                    "pull-raw",
                                    "energy",
                                    "--workspace-root",
                                    str(target_workspace),
                                    "--server-url",
                                    server_url,
                                ]
                            ),
                            0,
                        )
                    self.assertIn("Pulled raw workspace: energy", pull_stdout.getvalue())
                    self.assertTrue(
                        (
                            target_workspace
                            / "test-project"
                            / "loom"
                            / ".loom"
                            / "raw"
                            / "energy"
                            / "technology-data"
                            / "costs.csv"
                        ).exists()
                    )

    def test_pull_api_refreshes_changed_and_deleted_raw_files_incrementally(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_workspace = root / "source"
            target_workspace = root / "target"
            database_path = root / "loom.db"
            storage_root = root / "server-storage"

            self._write_energy_dataset(source_workspace, cost_value="10", include_legacy_file=True)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", "energy", "--workspace-root", str(source_workspace)]), 0)
                self.assertEqual(main(["confirm", "energy", "--workspace-root", str(source_workspace)]), 0)

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
                            main(
                                [
                                    "push",
                                    "energy",
                                    "--workspace-root",
                                    str(source_workspace),
                                    "--server-url",
                                    server_url,
                                ]
                            ),
                            0,
                        )

                    first_pull = loom.pull("energy", workspace_root=target_workspace, server_url=server_url)
                    self.assertEqual(first_pull[0].downloaded_file_count, 3)
                    self.assertEqual(first_pull[0].deleted_file_count, 0)

                    cached_costs = (
                        target_workspace
                        / "test-project"
                        / "loom"
                        / ".loom"
                        / "raw"
                        / "energy"
                        / "technology-data"
                        / "costs.csv"
                    )
                    cached_legacy = cached_costs.parent / "legacy.csv"
                    self.assertIn("solar,10", cached_costs.read_text(encoding="utf-8"))
                    self.assertTrue(cached_legacy.exists())

                    self._write_energy_dataset(source_workspace, cost_value="25", include_legacy_file=False)
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(
                            main(
                                [
                                    "push",
                                    "energy",
                                    "--workspace-root",
                                    str(source_workspace),
                                    "--server-url",
                                    server_url,
                                ]
                            ),
                            0,
                        )

                    second_pull = loom.pull("energy", workspace_root=target_workspace, server_url=server_url)
                    self.assertEqual(second_pull[0].downloaded_file_count, 1)
                    self.assertEqual(second_pull[0].deleted_file_count, 1)
                    self.assertIn("solar,25", cached_costs.read_text(encoding="utf-8"))
                    self.assertFalse(cached_legacy.exists())

    def test_pull_only_refreshes_cached_raw_files_and_writes_conflict_notice(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_workspace = root / "source"
            target_workspace = root / "target"
            database_path = root / "loom.db"
            storage_root = root / "server-storage"

            self._write_energy_dataset(source_workspace, cost_value="10", include_legacy_file=True)
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", "energy", "--workspace-root", str(source_workspace)]), 0)
                self.assertEqual(main(["confirm", "energy", "--workspace-root", str(source_workspace)]), 0)

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
                            main(["push", "energy", "--workspace-root", str(source_workspace), "--server-url", server_url]),
                            0,
                        )
                        self.assertEqual(
                            main(["pull", "energy", "--workspace-root", str(target_workspace), "--server-url", server_url]),
                            0,
                        )

                    cached_costs = loom.get(
                        "energy/technology-data/costs.csv",
                        workspace_root=target_workspace,
                        server_url=server_url,
                    )
                    self.assertTrue(cached_costs.exists())
                    cached_legacy = cached_costs.parent / "legacy.csv"
                    self.assertFalse(cached_legacy.exists())

                    local_raw_costs = (
                        target_workspace
                        / "test-project"
                        / "loom"
                        / "loom_raw"
                        / "energy"
                        / "technology-data"
                        / "costs.csv"
                    )
                    local_raw_costs.parent.mkdir(parents=True, exist_ok=True)
                    (local_raw_costs.parent / "loom.md").write_text("Energy dataset", encoding="utf-8")
                    local_raw_costs.write_text("tech,cost\nsolar,999\n", encoding="utf-8")

                    self._write_energy_dataset(source_workspace, cost_value="25", include_legacy_file=True)
                    with redirect_stdout(io.StringIO()):
                        self.assertEqual(main(["scan", "energy", "--workspace-root", str(source_workspace)]), 0)
                        self.assertEqual(main(["confirm", "energy", "--workspace-root", str(source_workspace)]), 0)
                        self.assertEqual(
                            main(["push", "energy", "--workspace-root", str(source_workspace), "--server-url", server_url]),
                            0,
                        )

                    pull_stdout = io.StringIO()
                    with redirect_stdout(pull_stdout):
                        self.assertEqual(
                            main(["pull", "energy", "--workspace-root", str(target_workspace), "--server-url", server_url]),
                            0,
                        )
                    self.assertIn("Raw conflict notice:", pull_stdout.getvalue())
                    self.assertIn("solar,25", cached_costs.read_text(encoding="utf-8"))
                    self.assertFalse(cached_legacy.exists())

                    notice_path = local_raw_costs.parent / "loom.raw-conflict.md"
                    self.assertTrue(notice_path.exists())
                    self.assertIn("technology-data/costs.csv", notice_path.read_text(encoding="utf-8"))

    def _write_energy_dataset(
        self,
        workspace_root: Path,
        *,
        cost_value: str = "10",
        include_legacy_file: bool = False,
    ) -> Path:
        dataset_dir = workspace_root / "test-project" / "loom" / "loom_raw" / "energy" / "technology-data"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        (dataset_dir / "loom.md").write_text("Energy dataset", encoding="utf-8")
        raw_file = dataset_dir / "costs.csv"
        raw_file.write_text(
            textwrap.dedent(
                """\
                tech,cost
                solar,{cost_value}
                wind,20
                """
            ).format(cost_value=cost_value),
            encoding="utf-8",
        )
        legacy_file = dataset_dir / "legacy.csv"
        if include_legacy_file:
            legacy_file.write_text("year,value\n2020,1\n", encoding="utf-8")
        elif legacy_file.exists():
            legacy_file.unlink()
        return raw_file

    def _call_app(self, client: TestClient, method: str, url: str, payload):
        path = url.replace("http://loom.test", "")
        if method == "GET":
            response = client.get(path)
        elif method == "POST":
            response = client.post(path, json=payload)
        else:
            raise AssertionError(f"Unsupported method: {method}")
        self.assertLess(response.status_code, 400, response.text)
        return response.json()


if __name__ == "__main__":
    unittest.main()
