from __future__ import annotations

from pathlib import Path
from typing import Any


def build_direct_child_dataset_map(dataset_roots: list[Path]) -> dict[Path, list[Path]]:
    child_map = {root: [] for root in dataset_roots}
    for child in dataset_roots:
        parents = [root for root in dataset_roots if root != child and child.is_relative_to(root)]
        if not parents:
            continue
        parent = max(parents, key=lambda path: len(path.parts))
        child_map[parent].append(child)
    return {root: sorted(children) for root, children in child_map.items()}


def iter_dataset_csv_files(dataset_root: Path, all_roots: list[Path]) -> list[Path]:
    nested_roots = [root for root in all_roots if root != dataset_root and root.is_relative_to(dataset_root)]
    csv_paths: list[Path] = []
    for path in dataset_root.rglob("*.csv"):
        if any(path.is_relative_to(nested_root) for nested_root in nested_roots):
            continue
        csv_paths.append(path)
    return csv_paths


def build_child_dataset_summaries(
    dataset_root: Path,
    child_dataset_roots: dict[Path, list[Path]],
    root_relative_dirs: dict[Path, str],
    next_datasets: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    parent_relative_dir = root_relative_dirs[dataset_root]
    summaries: list[dict[str, Any]] = []
    for child_root in child_dataset_roots.get(dataset_root, []):
        child_relative_dir = root_relative_dirs[child_root]
        summary = dict(next_datasets[child_relative_dir]["summary"])
        summary["overview_file"] = (Path(child_relative_dir).relative_to(parent_relative_dir) / "overview.md").as_posix()
        summaries.append(summary)
    return summaries
