from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "loom" / "src"))

from loom.cli import main
from loom.server_config import get_base_url, set_base_url


class SetApiCommandTest(unittest.TestCase):
    def tearDown(self) -> None:
        set_base_url(None)

    def test_set_api_persists_base_url_for_future_processes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            stdout = io.StringIO()
            old_value = os.environ.get("LOOM_CONFIG_HOME")
            os.environ["LOOM_CONFIG_HOME"] = temp_dir
            try:
                with redirect_stdout(stdout):
                    exit_code = main(["set-api", "https://loom-api-free.onrender.com/"])
                self.assertEqual(exit_code, 0)
                self.assertIn("https://loom-api-free.onrender.com", stdout.getvalue())

                set_base_url(None)
                self.assertEqual(get_base_url(), "https://loom-api-free.onrender.com")
            finally:
                if old_value is None:
                    os.environ.pop("LOOM_CONFIG_HOME", None)
                else:
                    os.environ["LOOM_CONFIG_HOME"] = old_value


if __name__ == "__main__":
    unittest.main()
