from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom-server" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

from loom.scanner import scan_path_to_explore


class ScanIncrementalTest(unittest.TestCase):
    def test_rescan_skips_rebuild_when_only_mtime_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            dataset = workspace / "raw_data" / "energy" / "alpha"
            dataset.mkdir(parents=True)
            csv_path = dataset / "costs.csv"
            (dataset / "loom.md").write_text("alpha dataset", encoding="utf-8")
            csv_path.write_text("name,value\nx,1\n", encoding="utf-8")

            first_result = scan_path_to_explore("raw_data/energy", workspace, workspace="energy")
            self.assertEqual(len(first_result.rebuilt_dataset_dirs), 1)
            manifest_path = workspace / "loom" / "energy" / "scan-manifest.json"
            first_manifest = manifest_path.read_text(encoding="utf-8")

            time.sleep(0.02)
            os.utime(csv_path, None)
            second_result = scan_path_to_explore("raw_data/energy", workspace, workspace="energy")

            self.assertEqual(len(second_result.rebuilt_dataset_dirs), 0)
            self.assertEqual(len(second_result.skipped_dataset_dirs), 1)
            self.assertEqual(manifest_path.read_text(encoding="utf-8"), first_manifest)

    def test_changed_csv_reuses_unchanged_csv_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            dataset = workspace / "raw_data" / "energy" / "alpha"
            dataset.mkdir(parents=True)
            (dataset / "loom.md").write_text("alpha dataset", encoding="utf-8")
            (dataset / "a.csv").write_text("name,value\nx,1\n", encoding="utf-8")
            (dataset / "b.csv").write_text("name,value\ny,2\n", encoding="utf-8")

            scan_path_to_explore("raw_data/energy", workspace, workspace="energy")
            profile_path = workspace / "loom" / "energy" / "alpha" / "profile.json"
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            profile["csv_profiles"][0]["cached_marker"] = "keep"
            profile_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")

            (dataset / "b.csv").write_text("name,value\ny,2\nz,3\n", encoding="utf-8")
            result = scan_path_to_explore("raw_data/energy", workspace, workspace="energy")

            self.assertEqual(len(result.rebuilt_dataset_dirs), 1)
            updated_profile = json.loads(profile_path.read_text(encoding="utf-8"))
            profiles = {item["file_name"]: item for item in updated_profile["csv_profiles"]}
            self.assertEqual(profiles["a.csv"]["cached_marker"], "keep")
            self.assertEqual(profiles["b.csv"]["row_count"], 2)

    def test_deleted_csv_removes_stale_generated_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            dataset = workspace / "raw_data" / "energy" / "alpha"
            dataset.mkdir(parents=True)
            (dataset / "loom.md").write_text("alpha dataset", encoding="utf-8")
            (dataset / "a.csv").write_text("name,value\nx,1\n", encoding="utf-8")
            stale_csv = dataset / "stale.csv"
            stale_csv.write_text("name,value\ny,2\n", encoding="utf-8")

            scan_path_to_explore("raw_data/energy", workspace, workspace="energy")
            target_dir = workspace / "loom" / "energy" / "alpha"
            unrelated_empty_dir = workspace / "loom" / "energy" / "manual-empty"
            unrelated_empty_dir.mkdir()
            manual_file = target_dir / "manual.txt"
            manual_file.write_text("keep me\n", encoding="utf-8")
            state_path = workspace / "loom" / ".loom" / "state" / "energy-scan.json"
            state = json.loads(state_path.read_text(encoding="utf-8"))
            generated_files = state["sources"]["raw_data/energy"]["datasets"]["alpha"]["generated_files"]
            generated_files.append("alpha/manual.txt")
            state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
            self.assertTrue((target_dir / "stale.card.md").exists())
            self.assertTrue((target_dir / "stale.profile.json").exists())

            stale_csv.unlink()
            scan_path_to_explore("raw_data/energy", workspace, workspace="energy")

            self.assertFalse((target_dir / "stale.card.md").exists())
            self.assertFalse((target_dir / "stale.profile.json").exists())
            self.assertTrue(manual_file.exists())
            self.assertTrue(unrelated_empty_dir.exists())

    def test_nested_csvs_with_same_name_get_distinct_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            dataset = workspace / "raw_data" / "energy" / "alpha"
            (dataset / "left").mkdir(parents=True)
            (dataset / "right").mkdir(parents=True)
            (dataset / "loom.md").write_text("alpha dataset", encoding="utf-8")
            (dataset / "left" / "costs.csv").write_text("name,value\nx,1\n", encoding="utf-8")
            (dataset / "right" / "costs.csv").write_text("name,value\ny,2\nz,3\n", encoding="utf-8")

            scan_path_to_explore("raw_data/energy", workspace, workspace="energy")

            target_dir = workspace / "loom" / "energy" / "alpha"
            self.assertTrue((target_dir / "left" / "costs.card.md").exists())
            self.assertTrue((target_dir / "right" / "costs.card.md").exists())
            left_card = (target_dir / "left" / "costs.card.md").read_text(encoding="utf-8")
            self.assertIn("CSV file: `left/costs.csv`", left_card)
            profile = json.loads((target_dir / "profile.json").read_text(encoding="utf-8"))
            profiles = {item["dataset_relative_path"]: item for item in profile["csv_profiles"]}
            self.assertEqual(profiles["left/costs.csv"]["row_count"], 1)
            self.assertEqual(profiles["right/costs.csv"]["row_count"], 2)


if __name__ == "__main__":
    unittest.main()
