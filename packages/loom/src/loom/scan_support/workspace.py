from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any


def resolve_workspace_relative_dir(raw_topic_dir: Path, dataset_root: Path, *, source_root_is_dataset: bool = False) -> str:
    relative_dir = dataset_root.relative_to(raw_topic_dir).as_posix() or "."
    if source_root_is_dataset and relative_dir != ".":
        return f"{raw_topic_dir.name}/{relative_dir}"
    return relative_dir if relative_dir != "." else raw_topic_dir.name


def normalize_previous_datasets(
    datasets: dict[str, dict[str, Any]],
    raw_topic_dir: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any] | None]:
    target_key = raw_topic_dir.name
    if "." not in datasets or target_key in datasets:
        return datasets, None
    normalized = dict(datasets)
    legacy_entry = normalized.pop(".")
    normalized[target_key] = legacy_entry
    return normalized, legacy_entry


def cleanup_legacy_root_dataset_outputs(explore_topic_dir: Path) -> None:
    if not explore_topic_dir.exists():
        return
    removable_names = {"datacard.md", "overview.md", "profile.json"}
    removable_suffixes = (".card.md", ".profile.json")
    for child in tuple(explore_topic_dir.iterdir()):
        if child.is_dir() or child.name in {"README.md", "scan-manifest.json"}:
            continue
        if child.name in removable_names or child.name.endswith(removable_suffixes):
            child.unlink()
    for child in tuple(explore_topic_dir.iterdir()):
        if child.is_dir() and not any(child.iterdir()):
            shutil.rmtree(child)
