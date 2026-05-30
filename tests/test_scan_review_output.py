from __future__ import annotations

import json
import sys
from pathlib import Path
import tempfile
import textwrap
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom-server" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

from loom.scanner import scan_path_to_explore


class ScanReviewOutputTest(unittest.TestCase):
    def test_scan_uses_loom_md_column_notes_in_cards(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            dataset_dir = workspace / "raw_data" / "cost" / "technology-data"
            dataset_dir.mkdir(parents=True)
            (dataset_dir / "loom.md").write_text(
                textwrap.dedent(
                    """\
                    source: https://example.com/costs

                    Manual cost modifications for selected technologies.

                    Columns:
                    - technology: technology or asset whose assumption is being updated
                    - parameter: parameter being modified for the technology
                    - value: numeric override for the parameter
                    - unit: unit attached to the override value
                    """
                ),
                encoding="utf-8",
            )
            (dataset_dir / "costs.csv").write_text(
                "technology,parameter,value,unit\nOCGT,investment,696,EUR2020/kW\n",
                encoding="utf-8",
            )

            scan_path_to_explore("raw_data/cost", workspace, workspace="cost")

            overview = (workspace / "loom" / "cost" / "technology-data" / "overview.md").read_text(encoding="utf-8")
            card = (workspace / "loom" / "cost" / "technology-data" / "costs.card.md").read_text(encoding="utf-8")
            profile = json.loads((workspace / "loom" / "cost" / "technology-data" / "profile.json").read_text(encoding="utf-8"))

            self.assertIn("Manual cost modifications for selected technologies.", overview)
            self.assertIn("Column roles:", overview)
            self.assertIn("## Column Roles", card)
            self.assertIn("technology or asset whose assumption is being updated", card)
            self.assertEqual(
                profile["csv_files"][0]["column_roles"]["technology"],
                "technology or asset whose assumption is being updated",
            )

    def test_scan_falls_back_to_common_column_role_hints(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            dataset_dir = workspace / "raw_data" / "cost" / "technology-data"
            dataset_dir.mkdir(parents=True)
            (dataset_dir / "loom.md").write_text("PyPSA cost table", encoding="utf-8")
            (dataset_dir / "costs.csv").write_text(
                "technology,parameter,value,unit,source,further description\nOCGT,investment,696,EUR2020/kW,DEA,manual override\n",
                encoding="utf-8",
            )

            scan_path_to_explore("raw_data/cost", workspace, workspace="cost")

            card = (workspace / "loom" / "cost" / "technology-data" / "costs.card.md").read_text(encoding="utf-8")

            self.assertIn("Metric or parameter name recorded for the technology in this row.", card)
            self.assertIn("Primary numeric value recorded for the row.", card)
            self.assertIn("Source or provenance for the value in this row.", card)


if __name__ == "__main__":
    unittest.main()
