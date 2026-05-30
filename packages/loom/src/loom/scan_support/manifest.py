from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..scan_state import hash_file, hash_text


def build_dataset_scan_manifest(
    raw_topic_dir: Path,
    dataset_root: Path,
    loom_text: str,
    csv_files: list[Path],
    previous_manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    scan_manifest, _ = build_dataset_scan_artifacts(raw_topic_dir, dataset_root, loom_text, csv_files, previous_manifest)
    return scan_manifest


def build_dataset_scan_artifacts(
    raw_topic_dir: Path,
    dataset_root: Path,
    loom_text: str,
    csv_files: list[Path],
    previous_file_cache: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    topic_relative_dir = dataset_root.relative_to(raw_topic_dir).as_posix() or "."
    workspace_relative_dir = topic_relative_dir if topic_relative_dir != "." else raw_topic_dir.name
    previous_csv_entries = _index_previous_csv_entries(previous_file_cache)
    csv_entries = []
    cache_entries = []
    for csv_path in csv_files:
        csv_entry, cache_entry = _build_csv_entries(raw_topic_dir, dataset_root, csv_path, previous_csv_entries)
        csv_entries.append(csv_entry)
        cache_entries.append(cache_entry)
    dataset_hash_source = {
        "raw_dataset_dir": topic_relative_dir,
        "loom_md_sha256": hash_text(loom_text),
        "csv_files": [{"topic_relative_path": entry["topic_relative_path"], "sha256": entry["sha256"]} for entry in csv_entries],
    }
    scan_manifest = {
        "raw_dataset_dir": topic_relative_dir,
        "topic_relative_dir": topic_relative_dir,
        "workspace_relative_dir": workspace_relative_dir,
        "loom_md_path": f"{topic_relative_dir}/loom.md" if topic_relative_dir != "." else "loom.md",
        "loom_md_sha256": hash_text(loom_text),
        "csv_files": csv_entries,
        "dataset_sha256": hash_text(json.dumps(dataset_hash_source, sort_keys=True, ensure_ascii=False)),
    }
    return scan_manifest, {"csv_files": cache_entries}


def _build_csv_entries(
    raw_topic_dir: Path,
    dataset_root: Path,
    csv_path: Path,
    previous_csv_entries: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    topic_relative_path = csv_path.relative_to(raw_topic_dir).as_posix()
    dataset_relative_path = csv_path.relative_to(dataset_root).as_posix()
    stat = csv_path.stat()
    previous_entry = previous_csv_entries.get(topic_relative_path)
    sha = _reuse_previous_sha(previous_entry, stat) or hash_file(csv_path)
    csv_entry = {
        "raw_path": topic_relative_path,
        "topic_relative_path": topic_relative_path,
        "dataset_relative_path": dataset_relative_path,
        "sha256": sha,
        "size_bytes": stat.st_size,
    }
    cache_entry = {
        "topic_relative_path": topic_relative_path,
        "dataset_relative_path": dataset_relative_path,
        "sha256": sha,
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
        "ctime_ns": stat.st_ctime_ns,
    }
    return csv_entry, cache_entry


def _index_previous_csv_entries(previous_manifest: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(previous_manifest, dict):
        return {}
    entries = previous_manifest.get("csv_files")
    if not isinstance(entries, list):
        return {}
    return {
        entry["topic_relative_path"]: entry
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("topic_relative_path"), str)
    }


def _reuse_previous_sha(previous_entry: dict[str, Any] | None, stat_result) -> str | None:
    if not isinstance(previous_entry, dict):
        return None
    if previous_entry.get("size_bytes") != stat_result.st_size:
        return None
    if previous_entry.get("mtime_ns") != stat_result.st_mtime_ns:
        return None
    if previous_entry.get("ctime_ns") != stat_result.st_ctime_ns:
        return None
    sha = previous_entry.get("sha256")
    return sha if isinstance(sha, str) else None


def collect_generated_files(target_dir: Path, explore_topic_dir: Path) -> list[str]:
    if not target_dir.exists():
        return []
    return [path.relative_to(explore_topic_dir).as_posix() for path in sorted(target_dir.rglob("*")) if path.is_file()]


def write_topic_manifest(explore_topic_dir: Path, topic: str, datasets: dict[str, dict[str, Any]]) -> None:
    explore_topic_dir.mkdir(parents=True, exist_ok=True)
    payload = {
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
    (explore_topic_dir / "scan-manifest.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
