from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom-server" / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom" / "src"))

from loom.chat import is_fast_scan_command, parse_chat_request, parse_loom_command


class ParseChatRequestTest(unittest.TestCase):
    def test_detects_fast_scan_command(self) -> None:
        self.assertTrue(is_fast_scan_command("loom scan ./datasets/energy to energy"))
        self.assertFalse(is_fast_scan_command("loom scan"))
        self.assertFalse(is_fast_scan_command("Please scan ./datasets/energy with loom"))

    def test_matches_basic_scan_command(self) -> None:
        request = parse_chat_request("loom scan ./datasets/energy to energy")
        self.assertIsNotNone(request)
        assert request is not None
        self.assertEqual(request.source_path, "./datasets/energy")
        self.assertEqual(request.workspace, "energy")

    def test_fast_path_uses_recent_workspace_when_to_is_omitted(self) -> None:
        request = parse_chat_request("loom scan ./datasets/energy")
        self.assertIsNotNone(request)
        assert request is not None
        self.assertEqual(request.source_path, "./datasets/energy")
        self.assertIsNone(request.workspace)

    def test_matches_looser_phrasing(self) -> None:
        request = parse_chat_request("Please scan ./datasets/energy to energy with loom for me")
        self.assertIsNotNone(request)
        assert request is not None
        self.assertEqual(request.source_path, "./datasets/energy")
        self.assertEqual(request.workspace, "energy")

    def test_ignores_non_scan_messages(self) -> None:
        self.assertIsNone(parse_chat_request("show me energy"))

    def test_parses_confirm_command(self) -> None:
        request = parse_loom_command("loom confirm energy")
        self.assertIsNotNone(request)
        assert request is not None
        self.assertEqual(request.command, "confirm")
        self.assertEqual(request.workspace, "energy")

    def test_parses_push_without_workspace(self) -> None:
        request = parse_loom_command("loom push")
        self.assertIsNotNone(request)
        assert request is not None
        self.assertEqual(request.command, "push")
        self.assertIsNone(request.workspace)

    def test_parses_pull_command(self) -> None:
        request = parse_loom_command("loom pull energy")
        self.assertIsNotNone(request)
        assert request is not None
        self.assertEqual(request.command, "pull")
        self.assertEqual(request.workspace, "energy")

    def test_parses_ask_command(self) -> None:
        request = parse_loom_command("loom ask OCGT 的成本是多少")
        self.assertIsNotNone(request)
        assert request is not None
        self.assertEqual(request.command, "ask")
        self.assertEqual(request.query, "OCGT 的成本是多少")

    def test_parses_bare_loom_question_as_ask(self) -> None:
        request = parse_loom_command("loom OCGT 的成本是多少")
        self.assertIsNotNone(request)
        assert request is not None
        self.assertEqual(request.command, "ask")
        self.assertEqual(request.query, "OCGT 的成本是多少")

    def test_does_not_treat_init_as_ask(self) -> None:
        self.assertIsNone(parse_loom_command("loom init"))


if __name__ == "__main__":
    unittest.main()
