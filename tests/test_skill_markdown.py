from __future__ import annotations

from importlib.resources import files
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

from loom.cli_app.skill import SKILL_TEMPLATES, render_skill_markdown


class SkillMarkdownTest(unittest.TestCase):
    def test_skill_templates_are_stored_as_packaged_markdown(self) -> None:
        template_dir = files("loom.cli_app").joinpath("templates")

        for template_name in SKILL_TEMPLATES.values():
            self.assertTrue(template_dir.joinpath(template_name).is_file())
        self.assertFalse(template_dir.joinpath("loom_data_skill.md").is_file())

    def test_skill_includes_post_scan_review_requirements(self) -> None:
        markdown = render_skill_markdown(SKILL_TEMPLATES["loom-dataset-scan-review"])

        self.assertIn("preserving the source path and workspace exactly", markdown)
        self.assertIn("uv run loomcli scan-index <path> [to <workspace>]", markdown)
        self.assertIn("Do not substitute the tutorial path", markdown)
        self.assertIn("After `loomcli scan-index` finishes, do a real review", markdown)
        self.assertIn("Read each scanned dataset's source `loom.md`.", markdown)
        self.assertIn("what each column is for", markdown)
        self.assertIn("Do not suggest `loomcli confirm`", markdown)

    def test_lookup_skill_has_strict_lookup_boundaries(self) -> None:
        markdown = render_skill_markdown(SKILL_TEMPLATES["loom-local-data-lookup"])

        self.assertIn("The user writes `loom ask <question>`.", markdown)
        self.assertIn("The user writes bare `loom <question>`.", markdown)
        self.assertIn("project-local data facts", markdown)
        self.assertIn("Automatic local-data rule", markdown)
        self.assertIn("visualization, reports, or coding", markdown)
        self.assertIn("even if the user does not explicitly say `loom`", markdown)
        self.assertIn("before reading `raw_data` directly", markdown)
        self.assertIn("unsupported chat forms such as `loom init`, `loom get`, `loom set-api`, or `loom install`", markdown)
        self.assertIn("`loomcli ask` does not exist", markdown)
        self.assertIn("Answer from the raw data, not from card summaries alone.", markdown)
        self.assertNotIn("If the request sounds data-related", markdown)
        self.assertNotIn("any plain-language data question", markdown)

    def test_workspace_ops_skill_separates_chat_and_cli(self) -> None:
        markdown = render_skill_markdown(SKILL_TEMPLATES["loom-workspace-ops"])

        self.assertIn("`loom ...` is a user-facing chat instruction.", markdown)
        self.assertIn("`loomcli ...` is the executable CLI command.", markdown)
        self.assertIn("uv run loomcli init --agent <agent>", markdown)
        self.assertIn("Use the agent value that matches the current assistant.", markdown)
        self.assertIn("Unsupported chat forms", markdown)
        self.assertIn("Unsupported CLI forms", markdown)


if __name__ == "__main__":
    unittest.main()
