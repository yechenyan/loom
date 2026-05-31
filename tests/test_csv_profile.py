from __future__ import annotations

import sys
from pathlib import Path
import tempfile
import textwrap
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom-server" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

from loom.csv_profile import profile_csv


class CsvProfileTest(unittest.TestCase):
    def test_profiles_csv_columns_and_samples(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "sample.csv"
            csv_path.write_text(
                textwrap.dedent(
                    """\
                    name,value,flag
                    alpha,1,true
                    beta,2,false
                    gamma,,true
                    """
                ),
                encoding="utf-8",
            )

            profile = profile_csv(csv_path, sample_size=2)

        self.assertEqual(profile["row_count"], 3)
        self.assertEqual([column["name"] for column in profile["columns"]], ["name", "value", "flag"])
        self.assertEqual(len(profile["head"]), 2)
        self.assertEqual(len(profile["tail"]), 2)
        value_column = profile["columns"][1]
        self.assertEqual(value_column["empty_count"], 1)
        self.assertIn("numeric_stats", value_column)

    def test_handles_empty_csv(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "empty.csv"
            csv_path.write_text("", encoding="utf-8")
            profile = profile_csv(csv_path)

        self.assertEqual(profile["row_count"], 0)
        self.assertEqual(profile["notes"], ["File is empty."])

    def test_keeps_richer_head_and_tail_samples_for_markdown_trimming(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "sample.csv"
            rows = ["name,value"] + [f"item{i},{i}" for i in range(12)]
            csv_path.write_text("\n".join(rows) + "\n", encoding="utf-8")

            profile = profile_csv(csv_path, sample_size=10)

        self.assertEqual(len(profile["head"]), 10)
        self.assertEqual(len(profile["tail"]), 10)


if __name__ == "__main__":
    unittest.main()
