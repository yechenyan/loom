from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "loom" / "src"))

import loom
from loom.server_config import DEFAULT_LOCAL_SERVER_URL, get_base_url, resolve_base_url, set_base_url


class ServerConfigTest(unittest.TestCase):
    def tearDown(self) -> None:
        set_base_url(None)

    def test_defaults_to_local_url(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(resolve_base_url(None), DEFAULT_LOCAL_SERVER_URL)

    def test_reads_environment_url_when_present(self) -> None:
        with mock.patch.dict(os.environ, {"LOOM_SERVER_URL": "https://loom-api.onrender.com/"}, clear=True):
            self.assertEqual(get_base_url(), "https://loom-api.onrender.com")

    def test_set_base_url_updates_python_api_default(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            set_base_url("https://loom-api.onrender.com/")
            self.assertEqual(loom.get_base_url(), "https://loom-api.onrender.com")
            self.assertEqual(resolve_base_url(None), "https://loom-api.onrender.com")


if __name__ == "__main__":
    unittest.main()
