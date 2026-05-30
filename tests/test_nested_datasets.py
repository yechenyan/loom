from __future__ import annotations

import json
import sys
from pathlib import Path
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom-server" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

from loom.scanner import DuplicateDatasetPathError, scan_path_to_explore


class NestedDatasetTest(unittest.TestCase):
    def test_child_csv_change_refreshes_parent_dataset_reporting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            parent = workspace / "datasets" / "energy-source"
            child = parent / "child"
            child.mkdir(parents=True)

            (parent / "loom.md").write_text("parent", encoding="utf-8")
            (child / "loom.md").write_text("child", encoding="utf-8")
            (child / "child.csv").write_text("name,value\nx,1\n", encoding="utf-8")

            first_result = scan_path_to_explore("./datasets/energy-source", workspace, workspace="energy")
            self.assertEqual(len(first_result.rebuilt_dataset_dirs), 2)

            time.sleep(0.02)
            (child / "child.csv").write_text("name,value\nx,1\ny,2\n", encoding="utf-8")
            second_result = scan_path_to_explore("./datasets/energy-source", workspace, workspace="energy")

            parent_dir = (workspace / "loom" / "energy" / "energy-source").resolve()
            child_dir = (parent_dir / "child").resolve()
            rebuilt_dirs = {path.resolve() for path in second_result.rebuilt_dataset_dirs}
            self.assertEqual(rebuilt_dirs, {parent_dir, child_dir})
            self.assertEqual(second_result.skipped_dataset_dirs, ())
            parent_profile = json.loads((parent_dir / "profile.json").read_text(encoding="utf-8"))
            self.assertEqual(parent_profile["child_datasets"][0]["row_count"], 2)

    def test_workspace_prompts_when_sources_overlap_nested_dataset_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            source_a = workspace / "datasets" / "source-a" / "shared" / "child"
            source_b = workspace / "datasets" / "source-b" / "shared"
            source_a.mkdir(parents=True)
            source_b.mkdir(parents=True)
            (source_a / "loom.md").write_text("child", encoding="utf-8")
            (source_a / "a.csv").write_text("x\n1\n", encoding="utf-8")
            (source_b / "loom.md").write_text("parent", encoding="utf-8")
            (source_b / "b.csv").write_text("y\n2\n", encoding="utf-8")

            scan_path_to_explore("./datasets/source-a", workspace, workspace="energy")

            with self.assertRaises(DuplicateDatasetPathError) as error:
                scan_path_to_explore("./datasets/source-b", workspace, workspace="energy")

            self.assertIn("conflicting dataset paths", str(error.exception))
            self.assertIn("shared", str(error.exception))


if __name__ == "__main__":
    unittest.main()
