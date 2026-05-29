from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .chat import parse_chat_request
from .csv_profile import profile_csv
from .datacard import refresh_dataset_card, write_dataset_card, write_topic_index
from .explore_repo import ensure_explore_repo
from .raw_cache_support import resolve_raw_data_root
from .scan_state import load_recent_workspace, load_scan_state, save_recent_workspace, save_scan_state
from .scan_support import (
    build_dataset_scan_manifest,
    collect_generated_files,
    is_nested_under_other_root,
    iter_dataset_csv_files,
    normalize_scan_sources,
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


class DuplicateDatasetPathError(RuntimeError):
    pass


def scan_topic_from_chat(message: str, workspace_root: Path | str) -> ScanResult | None:
    request = parse_chat_request(message)
    if request is None:
        return None

    if request.source_path is None:
        return None

    return scan_path_to_explore(request.source_path, workspace_root, workspace=request.workspace)


def scan_path_to_explore(source_path: str | Path, workspace_root: Path | str, *, workspace: str | None = None) -> ScanResult:
    root = Path(workspace_root)
    raw_topic_dir = _resolve_scan_source_dir(source_path, root)
    resolved_workspace = _resolve_scan_workspace(root, raw_topic_dir, workspace)
    return _scan_resolved_source(raw_topic_dir, resolved_workspace, root)


def scan_topic_to_explore(topic: str, workspace_root: Path | str) -> ScanResult:
    root = Path(workspace_root)
    raw_topic_dir = resolve_raw_data_root(root) / topic
    return _scan_resolved_source(raw_topic_dir, topic, root)


def _scan_resolved_source(raw_topic_dir: Path, workspace: str, workspace_root: Path) -> ScanResult:
    explore_root_dir = ensure_explore_repo(workspace_root)
    explore_topic_dir = explore_root_dir / workspace

    if not raw_topic_dir.exists():
        raise FileNotFoundError(f"Scan source directory not found: {raw_topic_dir}")
    if not raw_topic_dir.is_dir():
        raise NotADirectoryError(f"Scan source must be a directory: {raw_topic_dir}")

    source_key = _build_source_key(raw_topic_dir, workspace_root)
    all_dataset_roots = sorted(loom_file.parent for loom_file in raw_topic_dir.rglob("loom.md"))
    dataset_roots = [root for root in all_dataset_roots if not is_nested_under_other_root(root, all_dataset_roots)]
    previous_sources = _normalize_loaded_sources(normalize_scan_sources(load_scan_state(workspace_root, workspace)), workspace_root)
    previous_datasets = previous_sources.get(source_key, {}).get("datasets", {})
    next_datasets: dict[str, dict[str, Any]] = {}
    dataset_summaries: list[dict[str, Any]] = []
    pending_rebuilds: list[dict[str, Any]] = []
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
            summary = {
                "relative_dir": relative_dir_text,
                "csv_file_count": len(csv_files),
                "row_count": 0,
                "status": "current",
            }
            pending_rebuilds.append(
                {
                    "target_dir": target_dir,
                    "dataset_root": dataset_root,
                    "relative_dir_text": relative_dir_text,
                    "loom_text": loom_text,
                    "csv_files": csv_files,
                    "scan_manifest": scan_manifest,
                }
            )
        else:
            summary = dict(previous_entry["summary"])
            summary["status"] = "current"
            refresh_dataset_card(target_dir, dataset_root, loom_text, scan_manifest)
            skipped_dirs.append(target_dir)

        next_datasets[relative_dir_text] = {
            "status": "current",
            "scan_manifest": scan_manifest,
            "summary": summary,
            "generated_files": list(previous_entry.get("generated_files", [])) if previous_entry is not None else [],
        }
        dataset_summaries.append(summary)

    conflicts = _find_dataset_conflicts(next_datasets, previous_sources, source_key)
    if conflicts:
        lines = [f"Workspace `{workspace}` already tracks conflicting dataset paths from other scan sources:"]
        lines.extend(f"- `{relative_dir}` from `{source_path}`" for relative_dir, source_path in conflicts)
        lines.append("Choose a different workspace or rename the dataset directory before scanning.")
        raise DuplicateDatasetPathError("\n".join(lines))

    for pending in pending_rebuilds:
        csv_profiles = [profile_csv(path) for path in pending["csv_files"]]
        write_dataset_card(
            pending["target_dir"],
            pending["dataset_root"],
            pending["loom_text"],
            csv_profiles,
            scan_manifest=pending["scan_manifest"],
        )
        summary = next_datasets[pending["relative_dir_text"]]["summary"]
        summary["row_count"] = sum(profile["row_count"] for profile in csv_profiles)
        next_datasets[pending["relative_dir_text"]]["generated_files"] = collect_generated_files(
            pending["target_dir"],
            explore_topic_dir,
        )
        rebuilt_dirs.append(pending["target_dir"])

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

    next_sources = dict(previous_sources)
    next_sources[source_key] = {"source_path": source_key, "datasets": next_datasets}
    merged_datasets = _merge_source_datasets(next_sources)
    write_topic_index(explore_topic_dir, workspace, [dict(entry["summary"]) for entry in merged_datasets.values()])
    write_topic_manifest(explore_topic_dir, workspace, merged_datasets)
    save_scan_state(workspace_root, workspace, {"topic": workspace, "sources": next_sources})
    save_recent_workspace(workspace_root, workspace)

    return ScanResult(
        topic=workspace,
        raw_topic_dir=raw_topic_dir,
        explore_topic_dir=explore_topic_dir,
        dataset_count=len(dataset_roots),
        dataset_dirs=tuple(explore_topic_dir / dataset["relative_dir"] for dataset in dataset_summaries if dataset["status"] == "current"),
        rebuilt_dataset_dirs=tuple(rebuilt_dirs),
        skipped_dataset_dirs=tuple(skipped_dirs),
        missing_dataset_dirs=tuple(sorted(missing_dataset_dirs)),
    )


def _resolve_scan_source_dir(source_path: str | Path, workspace_root: Path) -> Path:
    source = Path(source_path).expanduser()
    candidate = source if source.is_absolute() else (workspace_root / source)
    return candidate.resolve()


def _resolve_scan_workspace(workspace_root: Path, _: Path, requested_workspace: str | None) -> str:
    if requested_workspace:
        return requested_workspace

    return load_recent_workspace(workspace_root) or "temporary"


def _build_source_key(raw_topic_dir: Path, workspace_root: Path) -> str:
    resolved_workspace_root = workspace_root.resolve()
    try:
        return raw_topic_dir.relative_to(resolved_workspace_root).as_posix()
    except ValueError:
        return raw_topic_dir.as_posix()


def _normalize_loaded_sources(sources: dict[str, dict[str, Any]], workspace_root: Path) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for source in sources.values():
        source_path = source.get("source_path")
        if not isinstance(source_path, str) or not source_path.strip():
            continue
        source_key = _normalize_loaded_source_key(source_path, workspace_root)
        if source_key in normalized:
            normalized[source_key]["datasets"].update(source["datasets"])
            continue
        normalized[source_key] = {
            "source_path": source_key,
            "datasets": dict(source["datasets"]),
        }
    return normalized


def _normalize_loaded_source_key(source_path: str, workspace_root: Path) -> str:
    path = Path(source_path).expanduser()
    if path.is_absolute():
        inferred = _infer_workspace_relative_source_key(path, workspace_root)
        if inferred is not None:
            return inferred
        return _build_source_key(path.resolve(strict=False), workspace_root)
    return _build_source_key((workspace_root / path).resolve(strict=False), workspace_root)


def _infer_workspace_relative_source_key(source_path: Path, workspace_root: Path) -> str | None:
    resolved_workspace_root = workspace_root.resolve()
    try:
        return source_path.relative_to(resolved_workspace_root).as_posix()
    except ValueError:
        pass

    parts = source_path.parts
    for index in range(len(parts)):
        suffix = Path(*parts[index:])
        if len(suffix.parts) < 2:
            continue
        candidate = resolved_workspace_root / suffix
        if candidate.exists() and candidate.is_dir():
            return suffix.as_posix()
    return None


def _find_dataset_conflicts(
    next_datasets: dict[str, dict[str, Any]],
    previous_sources: dict[str, dict[str, Any]],
    source_key: str,
) -> list[tuple[str, str]]:
    conflicts: list[tuple[str, str]] = []
    for other_key, other_source in previous_sources.items():
        if other_key == source_key:
            continue
        for relative_dir in next_datasets:
            if relative_dir in other_source["datasets"]:
                conflicts.append((relative_dir, other_source["source_path"]))
    return sorted(conflicts)


def _merge_source_datasets(sources: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for source in sorted(sources.values(), key=lambda item: item["source_path"]):
        for relative_dir, entry in source["datasets"].items():
            if relative_dir in merged:
                raise DuplicateDatasetPathError(f"Dataset path conflict on `{relative_dir}` across scan sources.")
            merged[relative_dir] = entry
    return merged
