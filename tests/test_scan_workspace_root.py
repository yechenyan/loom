from __future__ import annotations

import json
import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom-server" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

from loom.scanner import scan_path_to_explore


class ScanWorkspaceRootTest(unittest.TestCase):
    def test_top_level_dataset_scans_into_named_subdirectory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            source_dir = workspace / "raw_data" / "cost"
            source_dir.mkdir(parents=True)
            (source_dir / "loom.md").write_text("Cost dataset", encoding="utf-8")
            (source_dir / "costs.csv").write_text("tech,cost\nsolar,10\n", encoding="utf-8")

            result = scan_path_to_explore("raw_data/cost", workspace, workspace="cost")

            self.assertEqual(tuple(path.resolve() for path in result.dataset_dirs), ((workspace / "loom" / "cost" / "cost").resolve(),))
            profile_path = workspace / "loom" / "cost" / "cost" / "profile.json"
            self.assertTrue(profile_path.exists())
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            self.assertEqual(profile["raw_dataset_dir"], "cost")
            self.assertEqual(profile["scan_manifest"]["topic_relative_dir"], ".")
            self.assertEqual(profile["scan_manifest"]["workspace_relative_dir"], "cost")
            self.assertFalse((workspace / "loom" / "cost" / "profile.json").exists())

    def test_rescan_migrates_legacy_root_outputs_into_named_subdirectory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            source_dir = workspace / "raw_data" / "cost"
            source_dir.mkdir(parents=True)
            (source_dir / "loom.md").write_text("Cost dataset", encoding="utf-8")
            (source_dir / "costs.csv").write_text("tech,cost\nsolar,10\n", encoding="utf-8")

            legacy_dir = workspace / "loom" / "cost"
            legacy_dir.mkdir(parents=True)
            (legacy_dir / "profile.json").write_text('{"raw_dataset_dir": "/tmp/legacy"}\n', encoding="utf-8")
            (legacy_dir / "overview.md").write_text("legacy overview\n", encoding="utf-8")
            (legacy_dir / "costs.card.md").write_text("legacy card\n", encoding="utf-8")
            state_dir = workspace / "loom" / ".loom" / "state"
            state_dir.mkdir(parents=True)
            (state_dir / "cost-scan.json").write_text(
                json.dumps(
                    {
                        "topic": "cost",
                        "sources": {
                            "raw_data/cost": {
                                "source_path": "raw_data/cost",
                                "datasets": {
                                    ".": {
                                        "status": "current",
                                        "summary": {"relative_dir": ".", "csv_file_count": 1, "row_count": 1, "status": "current"},
                                        "scan_manifest": {"topic_relative_dir": "."},
                                        "generated_files": ["profile.json", "overview.md", "costs.card.md"],
                                    }
                                },
                            }
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            scan_path_to_explore("raw_data/cost", workspace, workspace="cost")

            self.assertFalse((legacy_dir / "profile.json").exists())
            self.assertTrue((legacy_dir / "cost" / "profile.json").exists())
            manifest = json.loads((legacy_dir / "scan-manifest.json").read_text(encoding="utf-8"))
            self.assertEqual([entry["relative_dir"] for entry in manifest["datasets"]], ["cost"])


if __name__ == "__main__":
    unittest.main()
