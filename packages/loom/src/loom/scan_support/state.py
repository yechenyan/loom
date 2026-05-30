from __future__ import annotations

from pathlib import Path
from typing import Any


def should_rebuild_dataset(target_dir: Path, scan_manifest: dict[str, Any], previous_entry: dict[str, Any] | None) -> bool:
    if previous_entry is None or str(previous_entry.get("status")) != "current":
        return True
    previous_manifest = previous_entry.get("scan_manifest")
    if _dataset_signature(previous_manifest) != _dataset_signature(scan_manifest):
        return True
    return not (target_dir / "profile.json").exists() or not (target_dir / "overview.md").exists()


def _dataset_signature(scan_manifest: object) -> object:
    if not isinstance(scan_manifest, dict):
        return scan_manifest
    signature = scan_manifest.get("dataset_sha256")
    return signature if isinstance(signature, str) else scan_manifest


def normalize_dataset_state(datasets: object) -> dict[str, dict[str, Any]]:
    if not isinstance(datasets, dict):
        return {}
    return {
        key: value
        for key, value in datasets.items()
        if isinstance(key, str) and isinstance(value, dict) and "summary" in value and "scan_manifest" in value
    }


def normalize_scan_sources(state: object) -> dict[str, dict[str, Any]]:
    if not isinstance(state, dict):
        return {}

    sources = state.get("sources")
    if isinstance(sources, dict):
        normalized: dict[str, dict[str, Any]] = {}
        for key, value in sources.items():
            if not isinstance(key, str) or not isinstance(value, dict):
                continue
            source_path = value.get("source_path")
            if not isinstance(source_path, str) or not source_path.strip():
                continue
            normalized[key] = {
                "source_path": source_path,
                "datasets": normalize_dataset_state(value.get("datasets", {})),
            }
        return normalized

    legacy_source_path = state.get("source_path")
    legacy_datasets = normalize_dataset_state(state.get("datasets", {}))
    if isinstance(legacy_source_path, str) and legacy_source_path.strip():
        return {legacy_source_path: {"source_path": legacy_source_path, "datasets": legacy_datasets}}
    return {}
