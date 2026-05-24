from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout
from pathlib import Path
import textwrap
import unittest
from unittest import mock

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "loom" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "loom-server" / "src"))

from loom.cli import main
import loom.sync_client as sync_client


class LoomTestCase(unittest.TestCase):
    def call_main(self, argv: list[str]) -> tuple[int, str]:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = main(argv)
        return exit_code, stdout.getvalue()

    def patch_server(self, client: TestClient):
        return mock.patch.object(
            sync_client,
            "_request_json",
            side_effect=lambda method, url, payload=None: self.call_app(client, method, url, payload),
        )

    def call_app(self, client: TestClient, method: str, url: str, payload=None):
        path = url.replace("http://loom.test", "")
        response = client.request(method, path, json=payload)
        if response.status_code >= 400:
            raise RuntimeError(f"Server request failed ({response.status_code}): {response.text}")
        return dict(response.json())

    def write_energy_dataset(self, workspace_root: Path, *, cost_value: str = "10", include_legacy_file: bool = False) -> Path:
        dataset_dir = workspace_root / "test-project" / "loom" / "loom_raw" / "energy" / "technology-data"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        (dataset_dir / "loom.md").write_text("source: https://example.com/energy\n\nEnergy dataset", encoding="utf-8")
        raw_file = dataset_dir / "costs.csv"
        raw_file.write_text(textwrap.dedent("""\
            tech,cost
            solar,{cost_value}
            wind,20
            """).format(cost_value=cost_value), encoding="utf-8")
        legacy_file = dataset_dir / "legacy.csv"
        if include_legacy_file:
            legacy_file.write_text("year,value\n2020,1\n", encoding="utf-8")
        elif legacy_file.exists():
            legacy_file.unlink()
        return raw_file
