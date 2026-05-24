from __future__ import annotations

import sys
from pathlib import Path
import tempfile
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom_scan" / "src"))

from loom_scan.cli import main


class InstallCommandTest(unittest.TestCase):
    def test_install_writes_skill_file_and_initializes_explore_repo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            workspace_root = Path(temp_dir) / "workspace"

            exit_code = main(
                [
                    "install",
                    "--codex-home",
                    str(codex_home),
                    "--workspace-root",
                    str(workspace_root),
                ]
            )

            self.assertEqual(exit_code, 0)
            skill_path = codex_home / "skills" / "loom-scan" / "SKILL.md"
            self.assertTrue(skill_path.exists())
            content = skill_path.read_text(encoding="utf-8")
            self.assertIn("loom scan <topic>", content)
            self.assertIn(str(workspace_root / "scripts" / "loom.py"), content)

            explore_git_dir = workspace_root / "test-project" / "loom" / "loom_explore" / ".git"
            self.assertTrue(explore_git_dir.exists())


if __name__ == "__main__":
    unittest.main()
