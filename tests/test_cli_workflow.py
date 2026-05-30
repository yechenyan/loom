from __future__ import annotations

import io
import json
import sys
from pathlib import Path
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom-server" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

from loom.cli import DEFAULT_DATABASE_URL, main


class CliWorkflowTest(unittest.TestCase):
    def scan_command(self, source_path: str = "raw_data/energy", *, workspace: str | None = "energy") -> list[str]:
        command = ["scan-index", source_path]
        if workspace is not None:
            command.extend(["to", workspace])
        return command

    def test_default_database_url_uses_fixed_loom_user(self) -> None:
        self.assertEqual(DEFAULT_DATABASE_URL, "postgresql+psycopg2://loom@127.0.0.1:5432/loom")

    def test_scan_shows_pending_changes_and_confirm_commits_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            dataset_dir = workspace / "raw_data" / "energy" / "technology-data"
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

            scan_stdout = io.StringIO()
            with redirect_stdout(scan_stdout):
                exit_code = main([*self.scan_command(), "--workspace-root", str(workspace)])

            self.assertEqual(exit_code, 0)
            scan_output = scan_stdout.getvalue()
            self.assertIn("Pending changes:", scan_output)
            self.assertIn("energy/README.md", scan_output)
            self.assertIn("Confirm with: loomcli confirm energy", scan_output)

            status_stdout = io.StringIO()
            with redirect_stdout(status_stdout):
                exit_code = main(["status", "energy", "--workspace-root", str(workspace)])

            self.assertEqual(exit_code, 0)
            status_output = status_stdout.getvalue()
            self.assertIn("energy/README.md", status_output)
            self.assertIn("Last pulled revision: -", status_output)
            self.assertIn("Last pushed revision: -", status_output)

            confirm_stdout = io.StringIO()
            with redirect_stdout(confirm_stdout):
                exit_code = main(["confirm", "energy", "--workspace-root", str(workspace)])

            self.assertEqual(exit_code, 0)
            confirm_output = confirm_stdout.getvalue()
            self.assertIn("Confirmed changes for energy.", confirm_output)
            self.assertIn("Commit:", confirm_output)

            clean_status_stdout = io.StringIO()
            with redirect_stdout(clean_status_stdout):
                exit_code = main(["status", "energy", "--workspace-root", str(workspace)])

            self.assertEqual(exit_code, 0)
            self.assertIn("No pending changes.", clean_status_stdout.getvalue())

            profile_path = workspace / "loom" / "energy" / "technology-data" / "profile.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual(profile["csv_count"], 1)

    def test_second_scan_skips_unchanged_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            dataset_dir = workspace / "raw_data" / "energy" / "technology-data"
            dataset_dir.mkdir(parents=True)
            (dataset_dir / "loom.md").write_text("Energy dataset", encoding="utf-8")
            (dataset_dir / "costs.csv").write_text("tech,cost\nsolar,10\n", encoding="utf-8")

            with redirect_stdout(io.StringIO()):
                self.assertEqual(main([*self.scan_command(), "--workspace-root", str(workspace)]), 0)
                self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace)]), 0)

            second_scan_stdout = io.StringIO()
            with redirect_stdout(second_scan_stdout):
                exit_code = main([*self.scan_command(), "--workspace-root", str(workspace)])

            self.assertEqual(exit_code, 0)
            second_scan_output = second_scan_stdout.getvalue()
            self.assertIn("Datasets rebuilt: 0", second_scan_output)
            self.assertIn("Datasets skipped: 1", second_scan_output)
            self.assertIn("No pending changes detected after scan.", second_scan_output)

    def test_scan_requires_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["scan-index", "--workspace-root", str(workspace)])

            self.assertEqual(exit_code, 1)
            output = stdout.getvalue()
            self.assertIn("Missing scan path", output)

    def test_scan_without_workspace_uses_recent_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            energy_dir = workspace / "raw_data" / "energy" / "technology-data"
            alt_dir = workspace / "datasets" / "alt-source" / "alt-technology-data"
            energy_dir.mkdir(parents=True)
            alt_dir.mkdir(parents=True)

            (energy_dir / "loom.md").write_text("energy", encoding="utf-8")
            (energy_dir / "costs.csv").write_text("tech,cost\nsolar,10\n", encoding="utf-8")
            (alt_dir / "loom.md").write_text("energy", encoding="utf-8")
            (alt_dir / "costs.csv").write_text("tech,cost\nsolar,11\n", encoding="utf-8")

            with redirect_stdout(io.StringIO()):
                self.assertEqual(main([*self.scan_command(), "--workspace-root", str(workspace)]), 0)

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["scan-index", "datasets/alt-source", "--workspace-root", str(workspace)])

            self.assertEqual(exit_code, 0)
            self.assertIn("Scanned workspace: energy", stdout.getvalue())

    def test_scan_without_workspace_uses_demo_when_no_history_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            alt_dir = workspace / "datasets" / "alt-source" / "technology-data"
            alt_dir.mkdir(parents=True)

            (alt_dir / "loom.md").write_text("energy", encoding="utf-8")
            (alt_dir / "costs.csv").write_text("tech,cost\nsolar,11\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["scan-index", "datasets/alt-source", "--workspace-root", str(workspace)])

            self.assertEqual(exit_code, 0)
            self.assertIn("Scanned workspace: demo", stdout.getvalue())

    def test_public_cli_rejects_scan_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            stdout = io.StringIO()
            with redirect_stdout(stdout), self.assertRaises(SystemExit):
                main(["scan", "raw_data/energy", "--workspace-root", str(workspace)])

    def test_public_cli_accepts_scan_index_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            dataset_dir = workspace / "raw_data" / "energy" / "technology-data"
            dataset_dir.mkdir(parents=True)
            (dataset_dir / "loom.md").write_text("Energy dataset", encoding="utf-8")
            (dataset_dir / "costs.csv").write_text("tech,cost\nsolar,10\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["scan-index", "raw_data/energy", "to", "energy", "--workspace-root", str(workspace)])

            self.assertEqual(exit_code, 0)
            self.assertIn("Scanned workspace: energy", stdout.getvalue())
            self.assertTrue((workspace / "loom" / "energy" / "technology-data" / "profile.json").exists())

    def test_scan_reports_conflicting_dataset_paths_across_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            first_dir = workspace / "datasets" / "first" / "shared"
            second_dir = workspace / "datasets" / "second" / "shared"
            first_dir.mkdir(parents=True)
            second_dir.mkdir(parents=True)
            (first_dir / "loom.md").write_text("first", encoding="utf-8")
            (first_dir / "a.csv").write_text("x\n1\n", encoding="utf-8")
            (second_dir / "loom.md").write_text("second", encoding="utf-8")
            (second_dir / "b.csv").write_text("y\n2\n", encoding="utf-8")

            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan-index", "datasets/first", "to", "energy", "--workspace-root", str(workspace)]), 0)

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["scan-index", "datasets/second", "to", "energy", "--workspace-root", str(workspace)])

            self.assertEqual(exit_code, 1)
            self.assertIn("conflicting dataset paths", stdout.getvalue())
            self.assertIn("shared", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
