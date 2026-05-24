from __future__ import annotations

import contextlib
import io
import unittest
from unittest import mock

from loom.cli import main


class PackagingMetadataTest(unittest.TestCase):
    def test_server_commands_report_missing_server_package(self) -> None:
        stderr = io.StringIO()

        def raise_missing_server(_: str) -> None:
            error = ModuleNotFoundError("No module named 'loom_server'")
            error.name = "loom_server"
            raise error

        with mock.patch("loom.cli_app.main.importlib.import_module", side_effect=raise_missing_server):
            with contextlib.redirect_stderr(stderr):
                exit_code = main(["server-run"])

        self.assertEqual(exit_code, 1)
        self.assertIn("requires the separate 'loom-server' package", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
