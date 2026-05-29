from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..scan_state import hash_file, hash_text


def build_dataset_scan_manifest(raw_topic_dir: Path, dataset_root: Path, loom_text: str, csv_files: list[Path]) -> dict[str, Any]:
    topic_relative_dir = dataset_root.relative_to(raw_topic_dir).as_posix() or "."
    csv_entries = [
        {
            "raw_path": csv_path.relative_to(raw_topic_dir).as_posix(),
            "topic_relative_path": csv_path.relative_to(raw_topic_dir).as_posix(),
            "dataset_relative_path": csv_path.relative_to(dataset_root).as_posix(),
            "sha256": hash_file(csv_path),
            "size_bytes": csv_path.stat().st_size,
        }
        for csv_path in csv_files
    ]
    dataset_hash_source = {
        "raw_dataset_dir": topic_relative_dir,
        "loom_md_sha256": hash_text(loom_text),
        "csv_files": [{"topic_relative_path": entry["topic_relative_path"], "sha256": entry["sha256"]} for entry in csv_entries],
    }
    return {
        "raw_dataset_dir": topic_relative_dir,
        "topic_relative_dir": topic_relative_dir,
        "loom_md_path": f"{topic_relative_dir}/loom.md" if topic_relative_dir != "." else "loom.md",
        "loom_md_sha256": hash_text(loom_text),
        "csv_files": csv_entries,
        "dataset_sha256": hash_text(json.dumps(dataset_hash_source, sort_keys=True, ensure_ascii=False)),
    }


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
