from __future__ import annotations

import io
import json
import sys
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom-server" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

from loom.cli import main


class InitCommandTest(unittest.TestCase):
    def test_init_installs_tutorial_by_default_on_enter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            workspace_root = Path(temp_dir) / "workspace"
            stdout = io.StringIO()

            with patch("builtins.input", side_effect=["1", "max", "", ""]), redirect_stdout(stdout):
                exit_code = main(["init", "--codex-home", str(codex_home), "--workspace-root", str(workspace_root)])

            self.assertEqual(exit_code, 0)
            self.assertIn("Tutorial data installed at:", stdout.getvalue())
            tutorial_dir = workspace_root / "raw_data" / "cost"
            self.assertTrue((tutorial_dir / "loom.md").exists())

    def test_init_creates_selected_skill_default_workspace_and_tutorial_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            workspace_root = Path(temp_dir) / "workspace"
            stdout = io.StringIO()

            with patch("builtins.input", side_effect=["1", "max", "y", ""]), redirect_stdout(stdout):
                exit_code = main(["init", "--codex-home", str(codex_home), "--workspace-root", str(workspace_root)])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("Initialized Loom workspace at:", output)
            self.assertIn("Next, send one of these messages in your AI agent chat.", output)
            self.assertIn("Loom now uses three names: `loom` for chat, `loomcli` for terminal commands, and `loomrun` for internal agent execution.", output)
            self.assertIn("Do not run the `loom ...` lines as shell commands.", output)
            self.assertIn('loom scan raw_data/cost to cost', output)
            self.assertIn('loom ask "What is the capex for OCGT?"', output)
            self.assertIn("What is the capex for OCGT?", output)
            self.assertIn("loomcli confirm cost", output)
            self.assertIn("loomcli push cost", output)

            skill_path = codex_home / "skills" / "loom-data" / "SKILL.md"
            self.assertTrue(skill_path.exists())
            skill_text = skill_path.read_text(encoding="utf-8")
            self.assertIn("`loom ...` means a user-facing chat instruction.", skill_text)
            self.assertIn("`loomcli ...` means an explicit terminal command", skill_text)
            self.assertIn("When the user writes `loom scan ...` in chat, treat it as a chat request", skill_text)
            self.assertIn("If the user writes `loom ask <question>` or `loom <question>`, do not run a lookup script for them.", skill_text)
            self.assertIn("`loom` is the chat trigger phrase.", skill_text)

            self.assertTrue((workspace_root / ".agents" / "skills" / "loom-data" / "SKILL.md").exists())
            self.assertFalse((workspace_root / ".claude" / "skills" / "loom-data" / "SKILL.md").exists())
            self.assertFalse((workspace_root / ".cursor" / "skills" / "loom-data" / "SKILL.md").exists())
            self.assertFalse((workspace_root / ".copilot" / "skills" / "loom-data" / "SKILL.md").exists())

            explore_git_dir = workspace_root / "loom" / ".git"
            self.assertTrue(explore_git_dir.exists())
            self.assertTrue((workspace_root / "loom" / "max").exists())

            recent_workspace_path = workspace_root / "loom" / ".loom" / "state" / "recent-workspace.json"
            recent_workspace = json.loads(recent_workspace_path.read_text(encoding="utf-8"))
            self.assertEqual(recent_workspace["workspace"], "max")

            tutorial_dir = workspace_root / "raw_data" / "cost"
            self.assertTrue((tutorial_dir / "loom.md").exists())
            self.assertTrue((tutorial_dir / "costs_2040-modifications.csv").exists())

    def test_init_menu_can_install_single_skill_when_loom_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            workspace_root = Path(temp_dir) / "workspace"
            (workspace_root / "loom").mkdir(parents=True)
            stdout = io.StringIO()

            with patch("builtins.input", side_effect=["2", "2"]), redirect_stdout(stdout):
                exit_code = main(["init", "--codex-home", str(codex_home), "--workspace-root", str(workspace_root)])

            self.assertEqual(exit_code, 0)
            self.assertIn("Skill installation finished.", stdout.getvalue())
            self.assertTrue((workspace_root / ".claude" / "skills" / "loom-data" / "SKILL.md").exists())
            self.assertFalse((codex_home / "skills" / "loom-data" / "SKILL.md").exists())
            self.assertFalse((workspace_root / ".agents" / "skills" / "loom-data" / "SKILL.md").exists())

    def test_init_menu_can_create_new_default_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            workspace_root = Path(temp_dir) / "workspace"
            (workspace_root / "loom").mkdir(parents=True)
            stdout = io.StringIO()

            with patch("builtins.input", side_effect=["3", "delta"]), redirect_stdout(stdout):
                exit_code = main(["init", "--codex-home", str(codex_home), "--workspace-root", str(workspace_root)])

            self.assertEqual(exit_code, 0)
            self.assertIn("Created a new default workspace: delta", stdout.getvalue())
            self.assertTrue((workspace_root / "loom" / "delta").exists())

            recent_workspace_path = workspace_root / "loom" / ".loom" / "state" / "recent-workspace.json"
            recent_workspace = json.loads(recent_workspace_path.read_text(encoding="utf-8"))
            self.assertEqual(recent_workspace["workspace"], "delta")

    def test_init_respects_agent_flag_without_prompting_for_agent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            workspace_root = Path(temp_dir) / "workspace"

            with patch("builtins.input", side_effect=["delta", "n"]):
                exit_code = main(
                    ["init", "--agent", "claude", "--codex-home", str(codex_home), "--workspace-root", str(workspace_root)]
                )

            self.assertEqual(exit_code, 0)
            skill_path = workspace_root / ".claude" / "skills" / "loom-data" / "SKILL.md"
            self.assertTrue(skill_path.exists())
            self.assertIn(
                "Use this skill whenever the user's request is about data:",
                skill_path.read_text(encoding="utf-8"),
            )


if __name__ == "__main__":
    unittest.main()
