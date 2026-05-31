from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..csv_profile import profile_csv


def build_incremental_csv_profiles(
    dataset_root: Path,
    target_dir: Path,
    csv_files: list[Path],
    scan_manifest: dict[str, Any],
    previous_entry: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    previous_profiles = _load_previous_profiles(target_dir)
    previous_csv_entries = _index_csv_entries(
        previous_entry.get("scan_manifest") if isinstance(previous_entry, dict) else None
    )
    current_csv_entries = _index_csv_entries(scan_manifest)

    profiles: list[dict[str, Any]] = []
    for csv_path in csv_files:
        relative_path = csv_path.relative_to(dataset_root).as_posix()
        current_entry = current_csv_entries.get(relative_path)
        previous_entry_for_file = previous_csv_entries.get(relative_path)
        cached_profile = previous_profiles.get(relative_path)
        if _can_reuse_profile(cached_profile, current_entry, previous_entry_for_file):
            profiles.append(_with_dataset_relative_path(cached_profile, relative_path))
            continue

        profile = profile_csv(csv_path)
        profiles.append(_with_dataset_relative_path(profile, relative_path))
    return profiles


def _load_previous_profiles(target_dir: Path) -> dict[str, dict[str, Any]]:
    profile_path = target_dir / "profile.json"
    if not profile_path.exists():
        return {}
    payload = json.loads(profile_path.read_text(encoding="utf-8"))
    profiles = payload.get("csv_profiles") if isinstance(payload, dict) else None
    if not isinstance(profiles, list):
        return {}

    indexed: dict[str, dict[str, Any]] = {}
    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        relative_path = profile.get("dataset_relative_path")
        if isinstance(relative_path, str) and relative_path:
            indexed[relative_path] = profile
            continue
        file_name = profile.get("file_name")
        if isinstance(file_name, str) and file_name:
            indexed[file_name] = profile
    return indexed


def _index_csv_entries(scan_manifest: object) -> dict[str, dict[str, Any]]:
    if not isinstance(scan_manifest, dict):
        return {}
    entries = scan_manifest.get("csv_files")
    if not isinstance(entries, list):
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        relative_path = entry.get("dataset_relative_path")
        if isinstance(relative_path, str) and relative_path:
            indexed[relative_path] = entry
    return indexed


def _can_reuse_profile(
    cached_profile: dict[str, Any] | None,
    current_entry: dict[str, Any] | None,
    previous_entry: dict[str, Any] | None,
) -> bool:
    if (
        not isinstance(cached_profile, dict)
        or not isinstance(current_entry, dict)
        or not isinstance(previous_entry, dict)
    ):
        return False
    return current_entry.get("sha256") == previous_entry.get("sha256")


def _with_dataset_relative_path(profile: dict[str, Any], relative_path: str) -> dict[str, Any]:
    normalized = dict(profile)
    normalized["dataset_relative_path"] = relative_path
    return normalized
