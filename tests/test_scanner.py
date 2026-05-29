from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
import tempfile
import textwrap
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom-server" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

from loom.scanner import DuplicateDatasetPathError, scan_path_to_explore, scan_topic_from_chat, scan_topic_to_explore


class ScannerTest(unittest.TestCase):
    def test_scans_topic_from_chat_message(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            dataset_dir = workspace / "datasets" / "energy-source" / "technology-data"
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

            result = scan_topic_from_chat("loom scan ./datasets/energy-source to energy", workspace)

            self.assertIsNotNone(result)
            assert result is not None
            self.assertEqual(result.dataset_count, 1)

            overview_path = workspace / "loom" / "energy" / "technology-data" / "overview.md"
            csv_card_path = workspace / "loom" / "energy" / "technology-data" / "costs.card.md"
            csv_profile_path = workspace / "loom" / "energy" / "technology-data" / "costs.profile.json"
            profile_path = workspace / "loom" / "energy" / "technology-data" / "profile.json"

            self.assertTrue(overview_path.exists())
            self.assertTrue(csv_card_path.exists())
            self.assertTrue(csv_profile_path.exists())
            self.assertTrue(profile_path.exists())

            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual(profile["csv_profiles"][0]["row_count"], 2)
            self.assertEqual(profile["csv_count"], 1)
            self.assertEqual(profile["total_row_count"], 2)
            self.assertEqual(profile["raw_dataset_dir"], "technology-data")
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
            raw_energy = workspace / "datasets" / "energy-source"
            parent = raw_energy / "parent"
            child = parent / "child"
            child.mkdir(parents=True)

            (parent / "loom.md").write_text("parent", encoding="utf-8")
            (child / "loom.md").write_text("child", encoding="utf-8")
            (parent / "parent.csv").write_text("a\n1\n", encoding="utf-8")
            (child / "child.csv").write_text("b\n2\n", encoding="utf-8")

            result = scan_path_to_explore("./datasets/energy-source", workspace, workspace="energy")

            self.assertEqual(result.dataset_count, 1)
            profile_path = workspace / "loom" / "energy" / "parent" / "profile.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual(len(profile["csv_profiles"]), 1)
            self.assertEqual(profile["csv_profiles"][0]["file_name"], "parent.csv")

            overview_path = workspace / "loom" / "energy" / "parent" / "overview.md"
            self.assertTrue(overview_path.exists())

    def test_skips_unchanged_dataset_and_keeps_missing_dataset_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            raw_energy = workspace / "datasets" / "energy-source"
            alpha = raw_energy / "alpha"
            beta = raw_energy / "beta"
            alpha.mkdir(parents=True)
            beta.mkdir(parents=True)

            (alpha / "loom.md").write_text("alpha dataset", encoding="utf-8")
            (beta / "loom.md").write_text("beta dataset", encoding="utf-8")
            (alpha / "alpha.csv").write_text("name,value\nx,1\n", encoding="utf-8")
            (beta / "beta.csv").write_text("name,value\ny,2\n", encoding="utf-8")

            first_result = scan_path_to_explore("./datasets/energy-source", workspace, workspace="energy")
            self.assertEqual(len(first_result.rebuilt_dataset_dirs), 2)
            self.assertEqual(len(first_result.skipped_dataset_dirs), 0)

            alpha_profile = (
                workspace / "loom" / "energy" / "alpha" / "profile.json"
            )
            alpha_profile_mtime = alpha_profile.stat().st_mtime_ns

            time.sleep(0.02)
            second_result = scan_path_to_explore("./datasets/energy-source", workspace, workspace="energy")
            self.assertEqual(len(second_result.rebuilt_dataset_dirs), 0)
            self.assertEqual(len(second_result.skipped_dataset_dirs), 2)
            self.assertEqual(alpha_profile.stat().st_mtime_ns, alpha_profile_mtime)

            (beta / "loom.md").unlink()

            time.sleep(0.02)
            third_result = scan_path_to_explore("./datasets/energy-source", workspace, workspace="energy")
            self.assertEqual(third_result.missing_dataset_dirs, ("beta",))

            topic_readme = (
                workspace / "loom" / "energy" / "README.md"
            ).read_text(encoding="utf-8")
            self.assertIn("`beta` [missing]", topic_readme)

            manifest = json.loads(
                (
                    workspace / "loom" / "energy" / "scan-manifest.json"
                ).read_text(encoding="utf-8")
            )
            beta_entry = next(entry for entry in manifest["datasets"] if entry["relative_dir"] == "beta")
            self.assertEqual(beta_entry["status"], "missing")
            self.assertTrue(
                (
                    workspace / "loom" / "energy" / "beta" / "beta.card.md"
                ).exists()
            )

    def test_scan_without_workspace_reuses_recent_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            legacy_dir = workspace / "raw_data" / "energy" / "technology-data"
            source_dir = workspace / "datasets" / "new-source" / "new-technology-data"
            legacy_dir.mkdir(parents=True)
            source_dir.mkdir(parents=True)
            (legacy_dir / "loom.md").write_text("Energy dataset", encoding="utf-8")
            (legacy_dir / "costs.csv").write_text("tech,cost\nsolar,9\n", encoding="utf-8")
            (source_dir / "loom.md").write_text("Energy dataset", encoding="utf-8")
            (source_dir / "costs.csv").write_text("tech,cost\nsolar,10\n", encoding="utf-8")

            scan_topic_to_explore("energy", workspace)

            result = scan_path_to_explore("./datasets/new-source", workspace)

            self.assertEqual(result.topic, "energy")
            self.assertTrue((workspace / "loom" / "energy" / "technology-data" / "profile.json").exists())
            self.assertTrue((workspace / "loom" / "energy" / "new-technology-data" / "profile.json").exists())

    def test_scan_without_workspace_uses_temporary_when_no_history_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            source_dir = workspace / "datasets" / "new-source" / "technology-data"
            source_dir.mkdir(parents=True)
            (source_dir / "loom.md").write_text("Energy dataset", encoding="utf-8")
            (source_dir / "costs.csv").write_text("tech,cost\nsolar,10\n", encoding="utf-8")

            result = scan_path_to_explore("./datasets/new-source", workspace)

            self.assertEqual(result.topic, "temporary")
            self.assertTrue((workspace / "loom" / "temporary" / "technology-data" / "profile.json").exists())

    def test_workspace_tracks_multiple_source_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            source_a = workspace / "datasets" / "source-a" / "alpha"
            source_b = workspace / "datasets" / "source-b" / "beta"
            source_a.mkdir(parents=True)
            source_b.mkdir(parents=True)
            (source_a / "loom.md").write_text("alpha", encoding="utf-8")
            (source_a / "a.csv").write_text("x\n1\n", encoding="utf-8")
            (source_b / "loom.md").write_text("beta", encoding="utf-8")
            (source_b / "b.csv").write_text("y\n2\n", encoding="utf-8")

            first_result = scan_path_to_explore("./datasets/source-a", workspace, workspace="energy")
            second_result = scan_path_to_explore("./datasets/source-b", workspace, workspace="energy")

            self.assertEqual(first_result.missing_dataset_dirs, ())
            self.assertEqual(second_result.missing_dataset_dirs, ())
            self.assertTrue((workspace / "loom" / "energy" / "alpha" / "profile.json").exists())
            self.assertTrue((workspace / "loom" / "energy" / "beta" / "profile.json").exists())

            manifest = json.loads((workspace / "loom" / "energy" / "scan-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(
                [(entry["relative_dir"], entry["status"]) for entry in manifest["datasets"]],
                [("alpha", "current"), ("beta", "current")],
            )

    def test_workspace_prompts_when_multiple_sources_share_dataset_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            source_a = workspace / "datasets" / "source-a" / "shared"
            source_b = workspace / "datasets" / "source-b" / "shared"
            source_a.mkdir(parents=True)
            source_b.mkdir(parents=True)
            (source_a / "loom.md").write_text("alpha", encoding="utf-8")
            (source_a / "a.csv").write_text("x\n1\n", encoding="utf-8")
            (source_b / "loom.md").write_text("beta", encoding="utf-8")
            (source_b / "b.csv").write_text("y\n2\n", encoding="utf-8")

            scan_path_to_explore("./datasets/source-a", workspace, workspace="energy")

            with self.assertRaises(DuplicateDatasetPathError) as error:
                scan_path_to_explore("./datasets/source-b", workspace, workspace="energy")

            self.assertIn("conflicting dataset paths", str(error.exception))
            self.assertIn("shared", str(error.exception))

    def test_conflicting_scan_does_not_modify_existing_workspace_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            source_a = workspace / "datasets" / "source-a" / "shared"
            source_b = workspace / "datasets" / "source-b" / "shared"
            source_a.mkdir(parents=True)
            source_b.mkdir(parents=True)
            (source_a / "loom.md").write_text("alpha", encoding="utf-8")
            (source_a / "a.csv").write_text("name,value\nold,1\n", encoding="utf-8")
            (source_b / "loom.md").write_text("beta", encoding="utf-8")
            (source_b / "b.csv").write_text("name,value\nnew,2\n", encoding="utf-8")

            scan_path_to_explore("./datasets/source-a", workspace, workspace="energy")
            profile_path = workspace / "loom" / "energy" / "shared" / "profile.json"
            card_path = workspace / "loom" / "energy" / "shared" / "a.card.md"
            before_profile = profile_path.read_text(encoding="utf-8")
            before_card = card_path.read_text(encoding="utf-8")

            with self.assertRaises(DuplicateDatasetPathError):
                scan_path_to_explore("./datasets/source-b", workspace, workspace="energy")

            self.assertEqual(profile_path.read_text(encoding="utf-8"), before_profile)
            self.assertEqual(card_path.read_text(encoding="utf-8"), before_card)
            self.assertFalse((workspace / "loom" / "energy" / "shared" / "b.card.md").exists())

    def test_scan_state_reuses_same_source_after_workspace_moves(self) -> None:
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            workspace_a = Path(first_dir)
            workspace_b = Path(second_dir)
            source_a = workspace_a / "datasets" / "source-a" / "alpha"
            source_b = workspace_b / "datasets" / "source-a" / "alpha"
            source_a.mkdir(parents=True)
            source_b.mkdir(parents=True)
            (source_a / "loom.md").write_text("alpha", encoding="utf-8")
            (source_a / "a.csv").write_text("x\n1\n", encoding="utf-8")
            (source_b / "loom.md").write_text("alpha", encoding="utf-8")
            (source_b / "a.csv").write_text("x\n1\n", encoding="utf-8")

            first_result = scan_path_to_explore("./datasets/source-a", workspace_a, workspace="energy")
            self.assertEqual(len(first_result.rebuilt_dataset_dirs), 1)

            shutil.copytree(workspace_a / "loom", workspace_b / "loom")

            second_result = scan_path_to_explore("./datasets/source-a", workspace_b, workspace="energy")

            self.assertEqual(len(second_result.rebuilt_dataset_dirs), 0)
            self.assertEqual(len(second_result.skipped_dataset_dirs), 1)
            profile = json.loads((workspace_b / "loom" / "energy" / "alpha" / "profile.json").read_text(encoding="utf-8"))
            overview = (workspace_b / "loom" / "energy" / "alpha" / "overview.md").read_text(encoding="utf-8")
            self.assertEqual(profile["raw_dataset_dir"], "alpha")
            self.assertIn("- Raw dataset path: `alpha`", overview)
            state = json.loads((workspace_b / "loom" / ".loom" / "state" / "energy-scan.json").read_text(encoding="utf-8"))
            self.assertEqual(sorted(state["sources"].keys()), ["datasets/source-a"])


if __name__ == "__main__":
    unittest.main()
