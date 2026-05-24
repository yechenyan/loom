from __future__ import annotations

import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages" / "loom_scan" / "src"))

from loom_scan.chat import is_fast_scan_command, parse_chat_request


class ParseChatRequestTest(unittest.TestCase):
    def test_detects_fast_scan_command(self) -> None:
        self.assertTrue(is_fast_scan_command("loom scan energy"))
        self.assertFalse(is_fast_scan_command("Please scan energy with loom for me"))

    def test_matches_basic_scan_command(self) -> None:
        request = parse_chat_request("loom scan energy")
        self.assertIsNotNone(request)
        assert request is not None
        self.assertEqual(request.topic, "energy")

    def test_fast_path_ignores_trailing_words_after_topic(self) -> None:
        request = parse_chat_request("loom scan energy please")
        self.assertIsNotNone(request)
        assert request is not None
        self.assertEqual(request.topic, "energy")

    def test_matches_looser_phrasing(self) -> None:
        request = parse_chat_request("Please scan energy with loom for me")
        self.assertIsNotNone(request)
        assert request is not None
        self.assertEqual(request.topic, "energy")

    def test_ignores_non_scan_messages(self) -> None:
        self.assertIsNone(parse_chat_request("show me energy"))


if __name__ == "__main__":
    unittest.main()
