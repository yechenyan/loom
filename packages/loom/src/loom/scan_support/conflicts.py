from __future__ import annotations

from pathlib import PurePosixPath
from typing import Any


def find_dataset_conflicts(
    next_datasets: dict[str, dict[str, Any]],
    previous_sources: dict[str, dict[str, Any]],
    source_key: str,
) -> list[tuple[str, str]]:
    conflicts: list[tuple[str, str]] = []
    for other_key, other_source in previous_sources.items():
        if other_key == source_key:
            continue
        for relative_dir in next_datasets:
            if any(_paths_overlap(relative_dir, other_dir) for other_dir in other_source["datasets"]):
                conflicts.append((relative_dir, other_source["source_path"]))
    return sorted(conflicts)


def _paths_overlap(left: str, right: str) -> bool:
    left_parts = _path_parts(left)
    right_parts = _path_parts(right)
    if not left_parts or not right_parts:
        return left_parts == right_parts
    return left_parts[: len(right_parts)] == right_parts or right_parts[: len(left_parts)] == left_parts


def _path_parts(path: str) -> tuple[str, ...]:
    return tuple(part for part in PurePosixPath(path).parts if part != ".")
