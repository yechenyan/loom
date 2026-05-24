from __future__ import annotations

from pathlib import Path
from typing import Any


def should_rebuild_dataset(target_dir: Path, scan_manifest: dict[str, Any], previous_entry: dict[str, Any] | None) -> bool:
    if previous_entry is None or str(previous_entry.get("status")) != "current":
        return True
    if previous_entry.get("scan_manifest") != scan_manifest:
        return True
    return not (target_dir / "profile.json").exists() or not (target_dir / "overview.md").exists()


def normalize_dataset_state(datasets: object) -> dict[str, dict[str, Any]]:
    if not isinstance(datasets, dict):
        return {}
    return {
        key: value
        for key, value in datasets.items()
        if isinstance(key, str) and isinstance(value, dict) and "summary" in value and "scan_manifest" in value
    }
