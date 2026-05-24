from __future__ import annotations

from pathlib import Path


def is_nested_under_other_root(candidate: Path, roots: list[Path]) -> bool:
    return any(other != candidate and candidate.is_relative_to(other) for other in roots)


def iter_dataset_csv_files(dataset_root: Path, all_roots: list[Path]) -> list[Path]:
    nested_roots = [root for root in all_roots if root != dataset_root and root.is_relative_to(dataset_root)]
    csv_paths: list[Path] = []
    for path in dataset_root.rglob("*.csv"):
        if any(path.is_relative_to(nested_root) for nested_root in nested_roots):
            continue
        csv_paths.append(path)
    return csv_paths
