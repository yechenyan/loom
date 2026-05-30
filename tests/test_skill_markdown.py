from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

from loom.cli_app.skill import render_skill_markdown


class SkillMarkdownTest(unittest.TestCase):
    def test_skill_includes_post_scan_review_requirements(self) -> None:
        workspace_root = Path("/tmp/loom-workspace")
        markdown = render_skill_markdown(
            workspace_root,
            workspace_root / "scripts" / "loomcli.py",
        )

        self.assertIn("After `loomcli scan-index` finishes, do a real review", markdown)
        self.assertIn("Read each scanned dataset's `loom.md`.", markdown)
        self.assertIn("what each column is for", markdown)
        self.assertIn("Do not suggest `loomcli confirm`", markdown)


if __name__ == "__main__":
    unittest.main()
