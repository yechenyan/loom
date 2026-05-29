from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .datacard_parts import (
    build_csv_card,
    build_csv_entry,
    build_dataset_overview,
    collect_source_sites,
    extract_source_info,
)


def write_dataset_card(
    dataset_dir: Path,
    raw_dataset_dir: Path,
    loom_text: str,
    csv_profiles: list[dict[str, Any]],
    scan_manifest: dict[str, Any] | None = None,
) -> None:
    dataset_dir.mkdir(parents=True, exist_ok=True)
    legacy_datacard = dataset_dir / "datacard.md"
    if legacy_datacard.exists():
        legacy_datacard.unlink()

    raw_dataset_path = _resolve_raw_dataset_path(raw_dataset_dir, scan_manifest)
    csv_entries = [build_csv_entry(profile) for profile in csv_profiles]
    source_info = extract_source_info(loom_text)
    source_info["key_sites"] = collect_source_sites(csv_profiles)
    profile_payload = {
        "raw_dataset_dir": raw_dataset_path,
        "loom_md_present": bool(loom_text.strip()),
        "source": source_info,
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

    overview_markdown = build_dataset_overview(raw_dataset_dir, raw_dataset_path, loom_text, csv_profiles)
    (dataset_dir / "overview.md").write_text(overview_markdown, encoding="utf-8")

    for profile in csv_profiles:
        stem = Path(profile["file_name"]).stem
        (dataset_dir / f"{stem}.profile.json").write_text(
            json.dumps(profile, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (dataset_dir / f"{stem}.card.md").write_text(
            build_csv_card(raw_dataset_path, profile),
            encoding="utf-8",
        )


def refresh_dataset_card(
    dataset_dir: Path,
    raw_dataset_dir: Path,
    loom_text: str,
    scan_manifest: dict[str, Any] | None,
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

    expected_raw_dataset_path = _resolve_raw_dataset_path(raw_dataset_dir, scan_manifest)
    if payload.get("raw_dataset_dir") == expected_raw_dataset_path:
        return False

    write_dataset_card(dataset_dir, raw_dataset_dir, loom_text, csv_profiles, scan_manifest=scan_manifest)
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
    relative_dir = scan_manifest.get("topic_relative_dir") if isinstance(scan_manifest, dict) else None
    if isinstance(relative_dir, str) and relative_dir:
        return relative_dir
    return raw_dataset_dir.as_posix()
def _render_csv_profile(profile: dict[str, Any]) -> list[str]:
    lines = [
        "## Profiling Details",
        "",
    ]

    if profile["notes"]:
        lines.append("Notes:")
        for note in profile["notes"]:
            lines.append(f"- {note}")
        lines.append("")

    if profile["columns"]:
        lines.append("Columns:")
        for column in profile["columns"]:
            type_counts = ", ".join(
                f"{name}={count}" for name, count in sorted(column["type_counts"].items())
            ) or "none"
            lines.append(
                f"- `{column['name']}`: non-empty={column['non_empty_count']}, "
                f"empty={column['empty_count']}, inferred={type_counts}"
            )
            numeric_stats = column.get("numeric_stats")
            if numeric_stats:
                lines.append(
                    f"  numeric stats: min={numeric_stats['min']}, "
                    f"max={numeric_stats['max']}, mean={numeric_stats['mean']}"
                )
            top_values = column.get("top_values")
            if top_values:
                rendered_values = ", ".join(
                    f"{item['value']} ({item['count']})" for item in top_values
                )
                lines.append(f"  top values: {rendered_values}")
        lines.append("")

    if profile["head"]:
        lines.extend(
            [
                "Head sample (first 5 rows):",
                "```json",
                json.dumps(profile["head"][:5], indent=2, ensure_ascii=False),
                "```",
                "",
            ]
        )

    if profile["tail"]:
        lines.extend(
            [
                "Tail sample (last 5 rows):",
                "```json",
                json.dumps(profile["tail"][-5:], indent=2, ensure_ascii=False),
                "```",
                "",
            ]
        )

    return lines
