from __future__ import annotations

import json
import sys
from pathlib import Path
import tempfile
import textwrap
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom-server" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

from loom.scanner import scan_topic_from_chat, scan_topic_to_explore


class ScannerTest(unittest.TestCase):
    def test_scans_topic_from_chat_message(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            dataset_dir = workspace / "test-project" / "loom" / "loom_raw" / "energy" / "technology-data"
            dataset_dir.mkdir(parents=True)
            (dataset_dir / "loom.md").write_text(
                "source: https://example.com/energy\n\nEnergy dataset\n\nLicense: CC-BY",
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

            result = scan_topic_from_chat("loom scan energy", workspace)

            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result.dataset_count, 1)

            overview_path = workspace / "test-project" / "loom" / "loom_explore" / "energy" / "technology-data" / "overview.md"
            csv_card_path = workspace / "test-project" / "loom" / "loom_explore" / "energy" / "technology-data" / "costs.card.md"
            csv_profile_path = workspace / "test-project" / "loom" / "loom_explore" / "energy" / "technology-data" / "costs.profile.json"
            profile_path = workspace / "test-project" / "loom" / "loom_explore" / "energy" / "technology-data" / "profile.json"

            self.assertTrue(overview_path.exists())
            self.assertTrue(csv_card_path.exists())
            self.assertTrue(csv_profile_path.exists())
            self.assertTrue(profile_path.exists())

            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual(profile["csv_profiles"][0]["row_count"], 2)
            self.assertEqual(profile["csv_count"], 1)
            self.assertEqual(profile["total_row_count"], 2)
            self.assertEqual(profile["source"]["url"], "https://example.com/energy")
            self.assertEqual(profile["source"]["summary"], "Energy dataset")
            self.assertEqual(profile["source"]["key_sites"], [])
            self.assertEqual(profile["csv_files"][0]["summary"], "This table appears to describe records organized around `tech`, `cost`.")
            self.assertEqual(profile["scan_manifest"]["csv_files"][0]["topic_relative_path"], "technology-data/costs.csv")
            self.assertIn("sha256", profile["scan_manifest"]["csv_files"][0])

            overview_text = overview_path.read_text(encoding="utf-8")
            self.assertIn("## Source", overview_text)
            self.assertIn("Primary source", overview_text)
            self.assertNotIn("## Source Notes", overview_text)
            self.assertIn("Summary:", overview_text)
            self.assertIn("costs.card.md", overview_text)

            csv_card_text = csv_card_path.read_text(encoding="utf-8")
            self.assertIn("Row layout", csv_card_text)
            self.assertIn("Head sample (first 5 rows):", csv_card_text)
            self.assertIn("Tail sample (last 5 rows):", csv_card_text)

    def test_uses_top_level_loom_md_as_dataset_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            raw_energy = workspace / "test-project" / "loom" / "loom_raw" / "energy"
            parent = raw_energy / "parent"
            child = parent / "child"
            child.mkdir(parents=True)

            (parent / "loom.md").write_text("parent", encoding="utf-8")
            (child / "loom.md").write_text("child", encoding="utf-8")
            (parent / "parent.csv").write_text("a\n1\n", encoding="utf-8")
            (child / "child.csv").write_text("b\n2\n", encoding="utf-8")

            result = scan_topic_to_explore("energy", workspace)

            self.assertEqual(result.dataset_count, 1)
            profile_path = workspace / "test-project" / "loom" / "loom_explore" / "energy" / "parent" / "profile.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual(len(profile["csv_profiles"]), 1)
            self.assertEqual(profile["csv_profiles"][0]["file_name"], "parent.csv")

            overview_path = workspace / "test-project" / "loom" / "loom_explore" / "energy" / "parent" / "overview.md"
            self.assertTrue(overview_path.exists())

    def test_skips_unchanged_dataset_and_keeps_missing_dataset_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            raw_energy = workspace / "test-project" / "loom" / "loom_raw" / "energy"
            alpha = raw_energy / "alpha"
            beta = raw_energy / "beta"
            alpha.mkdir(parents=True)
            beta.mkdir(parents=True)

            (alpha / "loom.md").write_text("alpha dataset", encoding="utf-8")
            (beta / "loom.md").write_text("beta dataset", encoding="utf-8")
            (alpha / "alpha.csv").write_text("name,value\nx,1\n", encoding="utf-8")
            (beta / "beta.csv").write_text("name,value\ny,2\n", encoding="utf-8")

            first_result = scan_topic_to_explore("energy", workspace)
            self.assertEqual(len(first_result.rebuilt_dataset_dirs), 2)
            self.assertEqual(len(first_result.skipped_dataset_dirs), 0)

            alpha_profile = (
                workspace / "test-project" / "loom" / "loom_explore" / "energy" / "alpha" / "profile.json"
            )
            alpha_profile_mtime = alpha_profile.stat().st_mtime_ns

            time.sleep(0.02)
            second_result = scan_topic_to_explore("energy", workspace)
            self.assertEqual(len(second_result.rebuilt_dataset_dirs), 0)
            self.assertEqual(len(second_result.skipped_dataset_dirs), 2)
            self.assertEqual(alpha_profile.stat().st_mtime_ns, alpha_profile_mtime)

            (beta / "loom.md").unlink()

            time.sleep(0.02)
            third_result = scan_topic_to_explore("energy", workspace)
            self.assertEqual(third_result.missing_dataset_dirs, ("beta",))

            topic_readme = (
                workspace / "test-project" / "loom" / "loom_explore" / "energy" / "README.md"
            ).read_text(encoding="utf-8")
            self.assertIn("`beta` [missing]", topic_readme)

            manifest = json.loads(
                (
                    workspace / "test-project" / "loom" / "loom_explore" / "energy" / "scan-manifest.json"
                ).read_text(encoding="utf-8")
            )
            beta_entry = next(entry for entry in manifest["datasets"] if entry["relative_dir"] == "beta")
            self.assertEqual(beta_entry["status"], "missing")
            self.assertTrue(
                (
                    workspace / "test-project" / "loom" / "loom_explore" / "energy" / "beta" / "beta.card.md"
                ).exists()
            )


if __name__ == "__main__":
    unittest.main()
