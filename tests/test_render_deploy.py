from __future__ import annotations

import argparse
import unittest

from loom.render_deploy import DEFAULT_API_NAME, DEFAULT_WEB_NAME, DeployError, find_service, selected_targets


SERVICES = [
    {
        "service": {
            "id": "srv-api",
            "name": DEFAULT_API_NAME,
            "serviceDetails": {"url": "https://api.example.com"},
        }
    },
    {
        "service": {
            "id": "srv-web",
            "name": DEFAULT_WEB_NAME,
            "serviceDetails": {"url": "https://web.example.com"},
        }
    },
]


class RenderDeployTest(unittest.TestCase):
    def test_find_service_reads_render_payload(self) -> None:
        target = find_service(SERVICES, DEFAULT_API_NAME)
        self.assertEqual(target.service_id, "srv-api")
        self.assertEqual(target.url, "https://api.example.com")

    def test_selected_targets_defaults_to_api_then_web(self) -> None:
        args = argparse.Namespace(
            api_service=DEFAULT_API_NAME,
            web_service=DEFAULT_WEB_NAME,
            api_only=False,
            web_only=False,
        )
        targets = selected_targets(args, SERVICES)
        self.assertEqual([target.name for target in targets], [DEFAULT_API_NAME, DEFAULT_WEB_NAME])

    def test_selected_targets_rejects_conflicting_flags(self) -> None:
        args = argparse.Namespace(
            api_service=DEFAULT_API_NAME,
            web_service=DEFAULT_WEB_NAME,
            api_only=True,
            web_only=True,
        )
        with self.assertRaises(DeployError):
            selected_targets(args, SERVICES)


if __name__ == "__main__":
    unittest.main()
