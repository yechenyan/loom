from __future__ import annotations

import unittest

from loom.sync_ops.raw import _select_paths


class RawPathSelectionTest(unittest.TestCase):
    def test_select_paths_accepts_requested_path_with_redundant_dataset_prefix(self) -> None:
        manifest = {
            "costs_2020.csv": {"sha256": "a", "size_bytes": 1},
            "loom.md": {"sha256": "b", "size_bytes": 1},
        }

        selected = _select_paths(None, "cost", manifest, ("cost/costs_2020.csv",), False)

        self.assertEqual(selected, ("costs_2020.csv",))

    def test_select_paths_rejects_ambiguous_suffix_match(self) -> None:
        manifest = {
            "alpha/costs.csv": {"sha256": "a", "size_bytes": 1},
            "beta/alpha/costs.csv": {"sha256": "b", "size_bytes": 1},
        }

        with self.assertRaisesRegex(FileNotFoundError, "ambiguous"):
            _select_paths(None, "cost", manifest, ("prefix/beta/alpha/costs.csv",), False)


if __name__ == "__main__":
    unittest.main()
