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
from loom.cli_app.parser import build_parser


SKILL_NAMES = (
    "loom-local-data-lookup",
    "loom-dataset-scan-review",
    "loom-workspace-ops",
)


class InitCommandTest(unittest.TestCase):
    def test_install_command_is_not_available(self) -> None:
        with self.assertRaises(SystemExit) as context:
            build_parser().parse_args(["install"])

        self.assertEqual(context.exception.code, 2)

    def test_init_installs_tutorial_by_default_on_enter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            workspace_root = Path(temp_dir) / "workspace"
            stdout = io.StringIO()

            with patch("builtins.input", side_effect=["1", "", "", ""]), redirect_stdout(stdout):
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

            with patch("builtins.input", side_effect=["1", "", "y", ""]), redirect_stdout(stdout):
                exit_code = main(["init", "--codex-home", str(codex_home), "--workspace-root", str(workspace_root)])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("Initialized Loom workspace at:", output)
            self.assertIn("Tell the user to keep these in AI chat:", output)
            self.assertIn("Loom now uses two names: `loom` for chat and `loomcli` for execution.", output)
            self.assertIn("Do not run the `loom ...` lines in your shell.", output)
            self.assertIn('loom scan raw_data/cost to cost', output)
            self.assertIn('loom ask "What is the capex for OCGT?"', output)
            self.assertIn("loom OCGT 的成本是多少", output)
            self.assertIn("loomcli scan-index raw_data/cost to cost", output)
            self.assertIn("loomcli confirm cost", output)
            self.assertIn("loomcli push cost", output)

            for skill_name in SKILL_NAMES:
                skill_path = codex_home / "skills" / skill_name / "SKILL.md"
                self.assertTrue(skill_path.exists())
                self.assertTrue((workspace_root / ".agents" / "skills" / skill_name / "SKILL.md").exists())
                self.assertFalse((workspace_root / ".claude" / "skills" / skill_name / "SKILL.md").exists())
                self.assertFalse((workspace_root / ".cursor" / "skills" / skill_name / "SKILL.md").exists())
                self.assertFalse((workspace_root / ".copilot" / "skills" / skill_name / "SKILL.md").exists())

            self.assertFalse((codex_home / "skills" / "loom-data" / "SKILL.md").exists())
            lookup_text = (codex_home / "skills" / "loom-local-data-lookup" / "SKILL.md").read_text(encoding="utf-8")
            scan_text = (codex_home / "skills" / "loom-dataset-scan-review" / "SKILL.md").read_text(encoding="utf-8")
            ops_text = (codex_home / "skills" / "loom-workspace-ops" / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("The user writes `loom ask <question>`.", lookup_text)
            self.assertIn("`loomcli ask` does not exist", lookup_text)
            self.assertIn("After `loomcli scan-index` finishes, do a real review", scan_text)
            self.assertIn("Do not suggest `loomcli confirm`", scan_text)
            self.assertIn("`loom ...` is a user-facing chat instruction.", ops_text)
            self.assertIn("Unsupported chat forms", ops_text)

            explore_git_dir = workspace_root / "loom" / ".git"
            self.assertTrue(explore_git_dir.exists())
            self.assertTrue((workspace_root / "loom" / "tempo").exists())

            recent_workspace_path = workspace_root / "loom" / ".loom" / "state" / "recent-workspace.json"
            recent_workspace = json.loads(recent_workspace_path.read_text(encoding="utf-8"))
            self.assertEqual(recent_workspace["workspace"], "tempo")

            tutorial_dir = workspace_root / "raw_data" / "cost"
            self.assertTrue((tutorial_dir / "loom.md").exists())
            self.assertTrue((tutorial_dir / "costs_2040-modifications.csv").exists())

    def test_init_menu_can_install_skills_when_loom_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            workspace_root = Path(temp_dir) / "workspace"
            (workspace_root / "loom").mkdir(parents=True)
            stdout = io.StringIO()

            with patch("builtins.input", side_effect=["2", "2"]), redirect_stdout(stdout):
                exit_code = main(["init", "--codex-home", str(codex_home), "--workspace-root", str(workspace_root)])

            self.assertEqual(exit_code, 0)
            self.assertIn("Loom skills installed.", stdout.getvalue())
            for skill_name in SKILL_NAMES:
                self.assertTrue((workspace_root / ".claude" / "skills" / skill_name / "SKILL.md").exists())
                self.assertFalse((codex_home / "skills" / skill_name / "SKILL.md").exists())
                self.assertFalse((workspace_root / ".agents" / "skills" / skill_name / "SKILL.md").exists())
            self.assertFalse((workspace_root / ".claude" / "skills" / "loom-data" / "SKILL.md").exists())

    def test_init_menu_reset_help_uses_cli_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            codex_home = Path(temp_dir) / ".codex"
            workspace_root = Path(temp_dir) / "workspace"
            (workspace_root / "loom").mkdir(parents=True)
            stdout = io.StringIO()

            with patch("builtins.input", side_effect=["1"]), redirect_stdout(stdout):
                exit_code = main(["init", "--codex-home", str(codex_home), "--workspace-root", str(workspace_root)])

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("`loomcli init`", output)
            self.assertNotIn("`loom init`", output)

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
            skill_path = workspace_root / ".claude" / "skills" / "loom-local-data-lookup" / "SKILL.md"
            self.assertTrue(skill_path.exists())
            self.assertIn(
                "project-local, source-backed dataset facts",
                skill_path.read_text(encoding="utf-8"),
            )
            self.assertTrue((workspace_root / ".claude" / "skills" / "loom-dataset-scan-review" / "SKILL.md").exists())
            self.assertTrue((workspace_root / ".claude" / "skills" / "loom-workspace-ops" / "SKILL.md").exists())
            self.assertFalse((workspace_root / ".claude" / "skills" / "loom-data" / "SKILL.md").exists())


if __name__ == "__main__":
    unittest.main()
