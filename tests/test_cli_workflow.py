from __future__ import annotations

import io
import json
import sys
from pathlib import Path
import tempfile
import textwrap
import unittest
from contextlib import redirect_stdout


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

from loom.cli import DEFAULT_DATABASE_URL, main


class CliWorkflowTest(unittest.TestCase):
    def test_default_database_url_uses_fixed_loom_user(self) -> None:
        self.assertEqual(DEFAULT_DATABASE_URL, "postgresql+psycopg2://loom@127.0.0.1:5432/loom")

    def test_scan_shows_pending_changes_and_confirm_commits_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            dataset_dir = workspace / "test-project" / "loom" / "loom_raw" / "energy" / "technology-data"
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
                exit_code = main(["scan", "energy", "--workspace-root", str(workspace)])

            self.assertEqual(exit_code, 0)
            scan_output = scan_stdout.getvalue()
            self.assertIn("Pending changes:", scan_output)
            self.assertIn("energy/README.md", scan_output)
            self.assertIn("confirm energy", scan_output)

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

            profile_path = workspace / "test-project" / "loom" / "loom_explore" / "energy" / "technology-data" / "profile.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual(profile["csv_count"], 1)

    def test_second_scan_skips_unchanged_dataset(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            dataset_dir = workspace / "test-project" / "loom" / "loom_raw" / "energy" / "technology-data"
            dataset_dir.mkdir(parents=True)
            (dataset_dir / "loom.md").write_text("Energy dataset", encoding="utf-8")
            (dataset_dir / "costs.csv").write_text("tech,cost\nsolar,10\n", encoding="utf-8")

            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(["scan", "energy", "--workspace-root", str(workspace)]), 0)
                self.assertEqual(main(["confirm", "energy", "--workspace-root", str(workspace)]), 0)

            second_scan_stdout = io.StringIO()
            with redirect_stdout(second_scan_stdout):
                exit_code = main(["scan", "energy", "--workspace-root", str(workspace)])

            self.assertEqual(exit_code, 0)
            second_scan_output = second_scan_stdout.getvalue()
            self.assertIn("Datasets rebuilt: 0", second_scan_output)
            self.assertIn("Datasets skipped: 1", second_scan_output)
            self.assertIn("No pending changes detected after scan.", second_scan_output)


if __name__ == "__main__":
    unittest.main()
