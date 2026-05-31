from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .datacard_parts import (
    build_csv_card,
    build_csv_entry,
    build_dataset_overview,
    collect_source_sites,
    csv_card_file,
    csv_profile_file,
    extract_source_info,
)


def write_dataset_card(
    dataset_dir: Path,
    raw_dataset_dir: Path,
    loom_text: str,
    csv_profiles: list[dict[str, Any]],
    scan_manifest: dict[str, Any] | None = None,
    child_datasets: list[dict[str, Any]] | None = None,
) -> None:
    dataset_dir.mkdir(parents=True, exist_ok=True)
    legacy_datacard = dataset_dir / "datacard.md"
    if legacy_datacard.exists():
        legacy_datacard.unlink()

    raw_dataset_path = _resolve_raw_dataset_path(raw_dataset_dir, scan_manifest)
    csv_entries = [build_csv_entry(profile, loom_text) for profile in csv_profiles]
    source_info = extract_source_info(loom_text)
    source_info["key_sites"] = collect_source_sites(csv_profiles)
    child_datasets = child_datasets or []
    profile_payload = {
        "raw_dataset_dir": raw_dataset_path,
        "loom_md_present": bool(loom_text.strip()),
        "source": source_info,
        "child_datasets": child_datasets,
        "csv_count": len(csv_profiles),
        "total_row_count": sum(profile["row_count"] for profile in csv_profiles),
        "csv_files": csv_entries,
        "csv_profiles": csv_profiles,
    }
    if scan_manifest is not None:
        profile_payload["scan_manifest"] = scan_manifest
    (dataset_dir / "profile.json").write_text(
        json.dumps(profile_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    overview_markdown = build_dataset_overview(raw_dataset_dir, raw_dataset_path, loom_text, csv_profiles, child_datasets)
    (dataset_dir / "overview.md").write_text(overview_markdown, encoding="utf-8")

    for profile in csv_profiles:
        profile_path = dataset_dir / csv_profile_file(profile)
        card_path = dataset_dir / csv_card_file(profile)
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        card_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text(
            json.dumps(profile, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        card_path.write_text(
            build_csv_card(raw_dataset_path, profile, loom_text),
            encoding="utf-8",
        )


def expected_dataset_generated_files(dataset_dir: Path, explore_topic_dir: Path, csv_profiles: list[dict[str, Any]]) -> list[str]:
    expected = [dataset_dir / "profile.json", dataset_dir / "overview.md"]
    for profile in csv_profiles:
        expected.extend([dataset_dir / csv_profile_file(profile), dataset_dir / csv_card_file(profile)])
    return [path.relative_to(explore_topic_dir).as_posix() for path in expected]


def remove_stale_generated_files(explore_topic_dir: Path, previous_files: list[str], expected_files: list[str]) -> None:
    stale_files = sorted(set(previous_files) - set(expected_files), reverse=True)
    stale_parents: set[Path] = set()
    for relative_path in stale_files:
        if not _is_generated_dataset_file(relative_path):
            continue
        path = explore_topic_dir / relative_path
        if path.is_file():
            path.unlink()
            stale_parents.add(path.parent)
    _remove_empty_generated_dirs(explore_topic_dir, stale_parents)


def _remove_empty_generated_dirs(explore_topic_dir: Path, stale_parents: set[Path]) -> None:
    for parent in sorted(stale_parents, key=lambda path: len(path.parts), reverse=True):
        current = parent
        while current != explore_topic_dir and current.is_dir() and not any(current.iterdir()):
            current.rmdir()
            current = current.parent


def _is_generated_dataset_file(relative_path: str) -> bool:
    name = Path(relative_path).name
    return name in {"profile.json", "overview.md"} or name.endswith((".card.md", ".profile.json"))


def refresh_dataset_card(
    dataset_dir: Path,
    raw_dataset_dir: Path,
    loom_text: str,
    scan_manifest: dict[str, Any] | None,
    child_datasets: list[dict[str, Any]] | None = None,
) -> bool:
    profile_path = dataset_dir / "profile.json"
    overview_path = dataset_dir / "overview.md"
    if not profile_path.exists() or not overview_path.exists():
        return False

    payload = json.loads(profile_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return False
    csv_profiles = payload.get("csv_profiles")
    if not isinstance(csv_profiles, list):
        return False

    expected_child_datasets = child_datasets or []
    expected_raw_dataset_path = _resolve_raw_dataset_path(raw_dataset_dir, scan_manifest)
    if payload.get("raw_dataset_dir") == expected_raw_dataset_path and payload.get("child_datasets", []) == expected_child_datasets:
        return False

    write_dataset_card(
        dataset_dir,
        raw_dataset_dir,
        loom_text,
        csv_profiles,
        scan_manifest=scan_manifest,
        child_datasets=expected_child_datasets,
    )
    return True


def write_topic_index(
    explore_topic_dir: Path,
    topic: str,
    datasets: list[dict[str, Any]],
) -> None:
    lines = [
        f"# Loom Explore: {topic}",
        "",
        "This directory contains generated dataset cards for the raw Loom datasets.",
        "",
        "## Datasets",
        "",
    ]

    if not datasets:
        lines.append("No datasets were discovered for this topic.")
    else:
        for dataset in datasets:
            relative_dir = dataset["relative_dir"]
            status = str(dataset.get("status", "current"))
            status_suffix = ""
            if status != "current":
                status_suffix = f" [{status}]"
            lines.append(
                f"- `{relative_dir}`{status_suffix}: {dataset['csv_file_count']} CSV files, "
                f"{dataset['row_count']} total rows in profiled CSVs"
            )
            lines.append(f"  overview: `{relative_dir}/overview.md`")

    lines.append("")
    (explore_topic_dir / "README.md").write_text("\n".join(lines), encoding="utf-8")


def _resolve_raw_dataset_path(raw_dataset_dir: Path, scan_manifest: dict[str, Any] | None) -> str:
    relative_dir = scan_manifest.get("workspace_relative_dir") if isinstance(scan_manifest, dict) else None
    if isinstance(relative_dir, str) and relative_dir and relative_dir != ".":
        return relative_dir
    topic_relative_dir = scan_manifest.get("topic_relative_dir") if isinstance(scan_manifest, dict) else None
    if isinstance(topic_relative_dir, str) and topic_relative_dir and topic_relative_dir != ".":
        return topic_relative_dir
    return raw_dataset_dir.as_posix()
