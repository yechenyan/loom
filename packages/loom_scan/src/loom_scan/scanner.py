from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .chat import parse_chat_request
from .csv_profile import profile_csv
from .datacard import write_dataset_card, write_topic_index
from .explore_repo import ensure_explore_repo


@dataclass(frozen=True)
class ScanResult:
    topic: str
    raw_topic_dir: Path
    explore_topic_dir: Path
    dataset_count: int
    dataset_dirs: tuple[Path, ...]


def scan_topic_from_chat(message: str, workspace_root: Path | str) -> ScanResult | None:
    request = parse_chat_request(message)
    if request is None:
        return None

    return scan_topic_to_explore(request.topic, workspace_root)


def scan_topic_to_explore(topic: str, workspace_root: Path | str) -> ScanResult:
    root = Path(workspace_root)
    raw_topic_dir = root / "test-project" / "loom" / "loom_raw" / topic
    explore_root_dir = ensure_explore_repo(root)
    explore_topic_dir = explore_root_dir / topic

    if not raw_topic_dir.exists():
        raise FileNotFoundError(f"Raw topic directory not found: {raw_topic_dir}")

    all_dataset_roots = sorted(loom_file.parent for loom_file in raw_topic_dir.rglob("loom.md"))
    dataset_roots = [root for root in all_dataset_roots if not _is_nested_under_other_root(root, all_dataset_roots)]
    dataset_summaries: list[dict[str, Any]] = []
    written_dirs: list[Path] = []

    for dataset_root in dataset_roots:
        loom_text = (dataset_root / "loom.md").read_text(encoding="utf-8")
        csv_files = sorted(_iter_dataset_csv_files(dataset_root, all_dataset_roots))
        csv_profiles = [profile_csv(path) for path in csv_files]

        relative_dir = dataset_root.relative_to(raw_topic_dir)
        target_dir = explore_topic_dir / relative_dir
        write_dataset_card(target_dir, dataset_root, loom_text, csv_profiles)

        dataset_summaries.append(
            {
                "relative_dir": "." if str(relative_dir) == "." else relative_dir.as_posix(),
                "csv_file_count": len(csv_files),
                "row_count": sum(profile["row_count"] for profile in csv_profiles),
            }
        )
        written_dirs.append(target_dir)

    write_topic_index(explore_topic_dir, topic, dataset_summaries)

    return ScanResult(
        topic=topic,
        raw_topic_dir=raw_topic_dir,
        explore_topic_dir=explore_topic_dir,
        dataset_count=len(dataset_roots),
        dataset_dirs=tuple(written_dirs),
    )
def _is_nested_under_other_root(candidate: Path, roots: list[Path]) -> bool:
    for other in roots:
        if other == candidate:
            continue
        if candidate.is_relative_to(other):
            return True
    return False


def _iter_dataset_csv_files(dataset_root: Path, all_roots: list[Path]) -> list[Path]:
    nested_roots = [root for root in all_roots if root != dataset_root and root.is_relative_to(dataset_root)]
    csv_paths: list[Path] = []

    for path in dataset_root.rglob("*.csv"):
        if any(path.is_relative_to(nested_root) for nested_root in nested_roots):
            continue
        csv_paths.append(path)

    return csv_paths
