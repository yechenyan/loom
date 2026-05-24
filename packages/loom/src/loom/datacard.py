from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any


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

    csv_entries = [_build_csv_entry(profile) for profile in csv_profiles]
    source_info = _extract_source_info(loom_text)
    source_info["key_sites"] = _collect_source_sites(csv_profiles)
    profile_payload = {
        "raw_dataset_dir": raw_dataset_dir.as_posix(),
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

    overview_markdown = _build_dataset_overview(raw_dataset_dir, loom_text, csv_profiles)
    (dataset_dir / "overview.md").write_text(overview_markdown, encoding="utf-8")

    for profile in csv_profiles:
        stem = Path(profile["file_name"]).stem
        (dataset_dir / f"{stem}.profile.json").write_text(
            json.dumps(profile, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        (dataset_dir / f"{stem}.card.md").write_text(
            _build_csv_card(raw_dataset_dir, profile),
            encoding="utf-8",
        )


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


def _build_dataset_overview(
    raw_dataset_dir: Path,
    loom_text: str,
    csv_profiles: list[dict[str, Any]],
) -> str:
    source_info = _extract_source_info(loom_text)
    source_sites = source_info["key_sites"] = _collect_source_sites(csv_profiles)
    lines = [
        f"# Dataset Overview: {raw_dataset_dir.name}",
        "",
        "## Overview",
        "",
        f"- Raw dataset path: `{raw_dataset_dir.as_posix()}`",
        f"- CSV files profiled: {len(csv_profiles)}",
        f"- Total rows across profiled CSV files: {sum(profile['row_count'] for profile in csv_profiles)}",
        "",
    ]

    if source_info["url"] or source_info["summary"] or loom_text.strip():
        lines.extend(
            [
                "## Source",
                "",
            ]
        )

        if source_info["url"]:
            lines.append(f"- Primary source: `{source_info['url']}`")
        if source_info["summary"]:
            lines.append(f"- Description: {source_info['summary']}")
        if source_info["license"]:
            lines.append(f"- License: {source_info['license']}")
        if source_info["notes"]:
            lines.append(f"- Notes: {source_info['notes']}")
        if source_sites:
            lines.append(
                "- Key source sites: " + ", ".join(f"`{site}`" for site in source_sites)
            )
        if source_info["url"] or source_info["summary"] or source_info["license"] or source_info["notes"] or source_sites:
            lines.append("")

    lines.extend(
        [
            "## CSV Files",
            "",
        ]
    )

    if not csv_profiles:
        lines.append("No CSV files were found inside this dataset.")
        lines.append("")
        return "\n".join(lines)

    for profile in csv_profiles:
        stem = Path(profile["file_name"]).stem
        lines.extend(
            [
                f"### `{profile['file_name']}`",
                "",
                f"- Rows: {profile['row_count']}",
                f"- File size: {profile['file_size_bytes']} bytes",
                f"- Columns: {_render_column_list(profile)}",
                f"- Summary: {_summarize_csv(profile)}",
                f"- Card: `{stem}.card.md`",
                f"- Machine-readable profile: `{stem}.profile.json`",
                "",
            ]
        )

    return "\n".join(lines)


def _build_csv_card(raw_dataset_dir: Path, profile: dict[str, Any]) -> str:
    lines = [
        f"# CSV Data Card: {profile['file_name']}",
        "",
        "## Overview",
        "",
        f"- Raw dataset path: `{raw_dataset_dir.as_posix()}`",
        f"- CSV file: `{profile['file_name']}`",
        f"- Rows: {profile['row_count']}",
        f"- File size: {profile['file_size_bytes']} bytes",
        f"- Delimiter: `{profile['dialect']['delimiter']}`",
        f"- Summary: {_summarize_csv(profile)}",
        f"- Row layout: {_describe_row_layout(profile)}",
        "",
        "## Structure",
        "",
    ]

    if profile["columns"]:
        lines.append(f"- Columns: {_render_column_list(profile)}")
        lines.append(f"- Row layout pattern: {_describe_row_layout(profile)}")
        lines.append("")
    else:
        lines.append("No columns were detected.")
        lines.append("")

    lines.extend(_render_csv_profile(profile))
    return "\n".join(lines)


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


def _build_csv_entry(profile: dict[str, Any]) -> dict[str, Any]:
    stem = Path(profile["file_name"]).stem
    return {
        "file_name": profile["file_name"],
        "row_count": profile["row_count"],
        "file_size_bytes": profile["file_size_bytes"],
        "column_count": len(profile["columns"]),
        "columns": [column["name"] for column in profile["columns"]],
        "summary": _summarize_csv(profile),
        "card_file": f"{stem}.card.md",
        "profile_file": f"{stem}.profile.json",
    }


def _render_column_list(profile: dict[str, Any]) -> str:
    if not profile["columns"]:
        return "none"
    return ", ".join(f"`{column['name']}`" for column in profile["columns"])


def _summarize_csv(profile: dict[str, Any]) -> str:
    columns = [column["name"] for column in profile["columns"]]
    if not columns:
        return "No columns were detected in this file."

    lead = ", ".join(f"`{name}`" for name in columns[:4])
    if {"technology", "parameter", "value"}.issubset(columns):
        return (
            f"This table looks like a technology parameter matrix with one row per "
            f"technology and parameter combination. Key fields include {lead}."
        )
    if {"date", "value"}.issubset(columns):
        return f"This table looks like a time series keyed by {lead}."
    if {"id", "name"}.issubset(columns):
        return f"This table looks like an entity list keyed by {lead}."
    return f"This table appears to describe records organized around {lead}."


def _describe_row_layout(profile: dict[str, Any]) -> str:
    columns = [column["name"] for column in profile["columns"]]
    if not columns:
        return "No row pattern could be inferred because no columns were detected."

    if {"technology", "parameter", "value"}.issubset(columns):
        if {"financial_case", "scenario"}.issubset(columns):
            return (
                "Rows appear grouped first by `technology`, then by `parameter`, with repeated "
                "`financial_case` and `scenario` variants for the same technology-parameter pair."
            )
        return (
            "Rows appear grouped by `technology`, with repeated `parameter` records describing "
            "different metrics for each technology."
        )

    if {"date", "value"}.issubset(columns):
        return "Rows likely progress along `date`, with one measurement record per timestamp."

    if {"id", "name"}.issubset(columns):
        return "Rows likely list one entity per record, keyed by `id` and described by `name`."

    dimension_columns = [
        column["name"]
        for column in profile["columns"]
        if column["type_counts"].get("string") and column["non_empty_count"] > 0
    ][:3]
    if dimension_columns:
        rendered = ", ".join(f"`{name}`" for name in dimension_columns)
        return f"Rows appear organized around the categorical fields {rendered}."

    return "No clear row ordering pattern could be inferred from the sampled records."


def _extract_source_info(loom_text: str) -> dict[str, str]:
    source_url = ""
    summary = ""
    license_text = ""
    notes = ""

    paragraphs = [part.strip() for part in loom_text.split("\n\n") if part.strip()]
    for paragraph in paragraphs:
        lower = paragraph.lower()
        if lower.startswith("source:"):
            source_url = paragraph.split(":", 1)[1].strip()
            continue
        if not summary and "licence" not in lower and "license" not in lower:
            summary = " ".join(paragraph.splitlines()).strip()
            continue
        if lower.startswith("licence") or lower.startswith("license"):
            license_text = " ".join(paragraph.splitlines()).strip()
            continue
        if not notes:
            notes = " ".join(paragraph.splitlines()).strip()

    return {
        "url": source_url,
        "summary": summary,
        "license": license_text,
        "notes": notes,
    }


def _collect_source_sites(csv_profiles: list[dict[str, Any]]) -> list[str]:
    counts: dict[str, int] = {}
    for profile in csv_profiles:
        for column in profile["columns"]:
            if column["name"] != "source":
                continue
            for item in column.get("top_values", []):
                for site in _extract_urls(item["value"]):
                    counts[site] = counts.get(site, 0) + item["count"]

    ranked_sites = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [site for site, _ in ranked_sites[:5]]


def _extract_urls(text: str) -> list[str]:
    matches = re.findall(r"https?://\S+", text)
    seen: list[str] = []
    for match in matches:
        cleaned = match.rstrip("`.;:>)\"]}'")
        if cleaned not in seen:
            seen.append(cleaned)
    return seen
