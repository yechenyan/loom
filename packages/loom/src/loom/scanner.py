from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .chat import parse_chat_request
from .csv_profile import profile_csv
from .datacard import write_dataset_card, write_topic_index
from .explore_repo import ensure_explore_repo
from .raw_cache_support import list_local_raw_workspaces, resolve_loom_root
from .scan_state import load_scan_state, save_scan_state
from .scan_support import (
    build_dataset_scan_manifest,
    collect_generated_files,
    is_nested_under_other_root,
    iter_dataset_csv_files,
    normalize_dataset_state,
    should_rebuild_dataset,
    write_topic_manifest,
)


@dataclass(frozen=True)
class ScanResult:
    topic: str
    raw_topic_dir: Path
    explore_topic_dir: Path
    dataset_count: int
    dataset_dirs: tuple[Path, ...]
    rebuilt_dataset_dirs: tuple[Path, ...]
    skipped_dataset_dirs: tuple[Path, ...]
    missing_dataset_dirs: tuple[str, ...]


def scan_topic_from_chat(message: str, workspace_root: Path | str) -> ScanResult | None:
    request = parse_chat_request(message)
    if request is None:
        return None

    return scan_topic_to_explore(request.topic, workspace_root)


def scan_topic_to_explore(topic: str, workspace_root: Path | str) -> ScanResult:
    root = Path(workspace_root)
    raw_topic_dir = resolve_loom_root(root) / "loom_raw" / topic
    explore_root_dir = ensure_explore_repo(root)
    explore_topic_dir = explore_root_dir / topic

    if not raw_topic_dir.exists():
        raise FileNotFoundError(f"Raw topic directory not found: {raw_topic_dir}")

    all_dataset_roots = sorted(loom_file.parent for loom_file in raw_topic_dir.rglob("loom.md"))
    dataset_roots = [root for root in all_dataset_roots if not is_nested_under_other_root(root, all_dataset_roots)]
    previous_state = load_scan_state(root, topic)
    previous_datasets = normalize_dataset_state(previous_state.get("datasets", {}))
    next_datasets: dict[str, dict[str, Any]] = {}
    dataset_summaries: list[dict[str, Any]] = []
    rebuilt_dirs: list[Path] = []
    skipped_dirs: list[Path] = []

    for dataset_root in dataset_roots:
        loom_text = (dataset_root / "loom.md").read_text(encoding="utf-8")
        relative_dir = dataset_root.relative_to(raw_topic_dir)
        relative_dir_text = "." if str(relative_dir) == "." else relative_dir.as_posix()
        target_dir = explore_topic_dir / relative_dir
        csv_files = sorted(iter_dataset_csv_files(dataset_root, all_dataset_roots))
        scan_manifest = build_dataset_scan_manifest(raw_topic_dir, dataset_root, loom_text, csv_files)
        previous_entry = previous_datasets.get(relative_dir_text)

        if should_rebuild_dataset(target_dir, scan_manifest, previous_entry):
            csv_profiles = [profile_csv(path) for path in csv_files]
            write_dataset_card(target_dir, dataset_root, loom_text, csv_profiles, scan_manifest=scan_manifest)
            summary = {
                "relative_dir": relative_dir_text,
                "csv_file_count": len(csv_files),
                "row_count": sum(profile["row_count"] for profile in csv_profiles),
                "status": "current",
            }
            rebuilt_dirs.append(target_dir)
        else:
            summary = dict(previous_entry["summary"])
            summary["status"] = "current"
            skipped_dirs.append(target_dir)

        generated_files = collect_generated_files(target_dir, explore_topic_dir)
        next_datasets[relative_dir_text] = {
            "status": "current",
            "scan_manifest": scan_manifest,
            "summary": summary,
            "generated_files": generated_files,
        }
        dataset_summaries.append(summary)

    missing_dataset_dirs: list[str] = []
    for relative_dir_text, previous_entry in previous_datasets.items():
        if relative_dir_text in next_datasets:
            continue
        missing_entry = dict(previous_entry)
        missing_entry["status"] = "missing"
        summary = dict(previous_entry["summary"])
        summary["status"] = "missing"
        missing_entry["summary"] = summary
        next_datasets[relative_dir_text] = missing_entry
        dataset_summaries.append(summary)
        missing_dataset_dirs.append(relative_dir_text)

    write_topic_index(explore_topic_dir, topic, dataset_summaries)
    write_topic_manifest(explore_topic_dir, topic, next_datasets)
    save_scan_state(root, topic, {"topic": topic, "datasets": next_datasets})

    return ScanResult(
        topic=topic,
        raw_topic_dir=raw_topic_dir,
        explore_topic_dir=explore_topic_dir,
        dataset_count=len(dataset_roots),
        dataset_dirs=tuple(explore_topic_dir / dataset["relative_dir"] for dataset in dataset_summaries if dataset["status"] == "current"),
        rebuilt_dataset_dirs=tuple(rebuilt_dirs),
        skipped_dataset_dirs=tuple(skipped_dirs),
        missing_dataset_dirs=tuple(sorted(missing_dataset_dirs)),
    )


def scan_all_topics_to_explore(workspace_root: Path | str) -> tuple[ScanResult, ...]:
    return tuple(scan_topic_to_explore(topic, workspace_root) for topic in list_local_raw_workspaces(workspace_root))
