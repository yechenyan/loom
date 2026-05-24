from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .chat import parse_chat_request
from .csv_profile import profile_csv
from .datacard import write_dataset_card, write_topic_index
from .explore_repo import ensure_explore_repo
from .scan_state import hash_file, hash_text, load_scan_state, save_scan_state


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
    raw_topic_dir = root / "test-project" / "loom" / "loom_raw" / topic
    explore_root_dir = ensure_explore_repo(root)
    explore_topic_dir = explore_root_dir / topic

    if not raw_topic_dir.exists():
        raise FileNotFoundError(f"Raw topic directory not found: {raw_topic_dir}")

    all_dataset_roots = sorted(loom_file.parent for loom_file in raw_topic_dir.rglob("loom.md"))
    dataset_roots = [root for root in all_dataset_roots if not _is_nested_under_other_root(root, all_dataset_roots)]
    previous_state = load_scan_state(root, topic)
    previous_datasets = _normalize_dataset_state(previous_state.get("datasets", {}))
    next_datasets: dict[str, dict[str, Any]] = {}
    dataset_summaries: list[dict[str, Any]] = []
    rebuilt_dirs: list[Path] = []
    skipped_dirs: list[Path] = []

    for dataset_root in dataset_roots:
        loom_text = (dataset_root / "loom.md").read_text(encoding="utf-8")
        relative_dir = dataset_root.relative_to(raw_topic_dir)
        relative_dir_text = "." if str(relative_dir) == "." else relative_dir.as_posix()
        target_dir = explore_topic_dir / relative_dir
        csv_files = sorted(_iter_dataset_csv_files(dataset_root, all_dataset_roots))
        scan_manifest = _build_dataset_scan_manifest(raw_topic_dir, dataset_root, loom_text, csv_files)
        previous_entry = previous_datasets.get(relative_dir_text)

        if _should_rebuild_dataset(target_dir, scan_manifest, previous_entry):
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

        generated_files = _collect_generated_files(target_dir, explore_topic_dir)
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
    _write_topic_manifest(explore_topic_dir, topic, next_datasets)
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


def _build_dataset_scan_manifest(
    raw_topic_dir: Path,
    dataset_root: Path,
    loom_text: str,
    csv_files: list[Path],
) -> dict[str, Any]:
    csv_entries: list[dict[str, Any]] = []
    for csv_path in csv_files:
        csv_entries.append(
            {
                "raw_path": csv_path.as_posix(),
                "topic_relative_path": csv_path.relative_to(raw_topic_dir).as_posix(),
                "dataset_relative_path": csv_path.relative_to(dataset_root).as_posix(),
                "sha256": hash_file(csv_path),
                "size_bytes": csv_path.stat().st_size,
            }
        )

    dataset_hash_source = {
        "raw_dataset_dir": dataset_root.as_posix(),
        "loom_md_sha256": hash_text(loom_text),
        "csv_files": [
            {
                "topic_relative_path": entry["topic_relative_path"],
                "sha256": entry["sha256"],
            }
            for entry in csv_entries
        ],
    }
    dataset_hash = hash_text(json.dumps(dataset_hash_source, sort_keys=True, ensure_ascii=False))
    return {
        "raw_dataset_dir": dataset_root.as_posix(),
        "topic_relative_dir": dataset_root.relative_to(raw_topic_dir).as_posix() or ".",
        "loom_md_path": (dataset_root / "loom.md").as_posix(),
        "loom_md_sha256": hash_text(loom_text),
        "csv_files": csv_entries,
        "dataset_sha256": dataset_hash,
    }


def _should_rebuild_dataset(
    target_dir: Path,
    scan_manifest: dict[str, Any],
    previous_entry: dict[str, Any] | None,
) -> bool:
    if previous_entry is None:
        return True
    if str(previous_entry.get("status")) != "current":
        return True
    previous_manifest = previous_entry.get("scan_manifest")
    if previous_manifest != scan_manifest:
        return True
    if not (target_dir / "profile.json").exists():
        return True
    if not (target_dir / "overview.md").exists():
        return True
    return False


def _collect_generated_files(target_dir: Path, explore_topic_dir: Path) -> list[str]:
    if not target_dir.exists():
        return []
    files: list[str] = []
    for path in sorted(target_dir.rglob("*")):
        if not path.is_file():
            continue
        files.append(path.relative_to(explore_topic_dir).as_posix())
    return files


def _normalize_dataset_state(datasets: object) -> dict[str, dict[str, Any]]:
    if not isinstance(datasets, dict):
        return {}
    normalized: dict[str, dict[str, Any]] = {}
    for key, value in datasets.items():
        if isinstance(key, str) and isinstance(value, dict) and "summary" in value and "scan_manifest" in value:
            normalized[key] = value
    return normalized


def _write_topic_manifest(explore_topic_dir: Path, topic: str, datasets: dict[str, dict[str, Any]]) -> None:
    explore_topic_dir.mkdir(parents=True, exist_ok=True)
    manifest_payload = {
        "topic": topic,
        "datasets": [
            {
                "relative_dir": relative_dir,
                "status": entry.get("status", "current"),
                "summary": entry.get("summary", {}),
                "scan_manifest": entry.get("scan_manifest", {}),
                "generated_files": entry.get("generated_files", []),
            }
            for relative_dir, entry in sorted(datasets.items())
        ],
    }
    (explore_topic_dir / "scan-manifest.json").write_text(
        json.dumps(manifest_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
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
