from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .source import collect_source_sites, describe_column_role, describe_row_layout, extract_column_descriptions, extract_source_info, render_column_list, render_column_role_list, render_column_role_summary, summarize_csv


def csv_card_file(profile: dict[str, Any]) -> str:
    return f"{_csv_output_stem(profile)}.card.md"


def csv_profile_file(profile: dict[str, Any]) -> str:
    return f"{_csv_output_stem(profile)}.profile.json"


def csv_source_path(profile: dict[str, Any]) -> str:
    relative_path = profile.get("dataset_relative_path")
    return relative_path if isinstance(relative_path, str) and relative_path else profile["file_name"]


def build_dataset_overview(
    raw_dataset_dir: Path,
    raw_dataset_path: str,
    loom_text: str,
    csv_profiles: list[dict[str, Any]],
    child_datasets: list[dict[str, Any]] | None = None,
) -> str:
    source_info = extract_source_info(loom_text)
    source_sites = source_info["key_sites"] = collect_source_sites(csv_profiles)
    child_datasets = child_datasets or []
    lines = [f"# Dataset Overview: {raw_dataset_dir.name}", "", "## Overview", "", f"- Raw dataset path: `{raw_dataset_path}`", f"- CSV files profiled: {len(csv_profiles)}", f"- Total rows across profiled CSV files: {sum(profile['row_count'] for profile in csv_profiles)}", ""]
    if source_info["url"] or source_info["summary"] or loom_text.strip():
        lines.extend(["## Source", ""])
        for label, value in (("Primary source", source_info["url"]), ("Description", source_info["summary"]), ("License", source_info["license"]), ("Notes", source_info["notes"])):
            if value:
                lines.append(f"- {label}: {value if label != 'Primary source' else f'`{value}`'}")
        if source_sites:
            lines.append("- Key source sites: " + ", ".join(f"`{site}`" for site in source_sites))
        lines.append("")
    if child_datasets:
        lines.extend(["## Child Datasets", ""])
        for child in child_datasets:
            status = str(child.get("status", "current"))
            status_suffix = "" if status == "current" else f" [{status}]"
            lines.append(
                f"- `{child['relative_dir']}`{status_suffix}: {child['csv_file_count']} CSV files, "
                f"{child['row_count']} total rows, overview `{child['overview_file']}`"
            )
        lines.append("")
    lines.extend(["## CSV Files", ""])
    if not csv_profiles:
        return "\n".join(lines + ["No CSV files were found inside this dataset.", ""])
    for profile in csv_profiles:
        lines.extend(
            [
                f"### `{csv_source_path(profile)}`",
                "",
                f"- Rows: {profile['row_count']}",
                f"- File size: {profile['file_size_bytes']} bytes",
                f"- Columns: {render_column_list(profile)}",
                f"- Column roles: {render_column_role_summary(profile, loom_text)}",
                f"- Summary: {summarize_csv(profile)}",
                f"- Card: `{csv_card_file(profile)}`",
                f"- Machine-readable profile: `{csv_profile_file(profile)}`",
                "",
            ]
        )
    return "\n".join(lines)


def build_csv_card(raw_dataset_path: str, profile: dict[str, Any], loom_text: str) -> str:
    lines = [f"# CSV Data Card: {csv_source_path(profile)}", "", "## Overview", "", f"- Raw dataset path: `{raw_dataset_path}`", f"- CSV file: `{csv_source_path(profile)}`", f"- Rows: {profile['row_count']}", f"- File size: {profile['file_size_bytes']} bytes", f"- Delimiter: `{profile['dialect']['delimiter']}`", f"- Summary: {summarize_csv(profile)}", f"- Row layout: {describe_row_layout(profile)}", "", "## Structure", ""]
    lines.extend([f"- Columns: {render_column_list(profile)}", f"- Row layout pattern: {describe_row_layout(profile)}", ""] if profile["columns"] else ["No columns were detected.", ""])
    if profile["columns"]:
        lines.extend(["## Column Roles", "", *render_column_role_list(profile, loom_text), ""])
    return "\n".join(lines + _render_csv_profile(profile))


def build_csv_entry(profile: dict[str, Any], loom_text: str) -> dict[str, Any]:
    descriptions = extract_column_descriptions(loom_text)
    return {
        "file_name": profile["file_name"],
        "dataset_relative_path": csv_source_path(profile),
        "row_count": profile["row_count"],
        "file_size_bytes": profile["file_size_bytes"],
        "column_count": len(profile["columns"]),
        "columns": [column["name"] for column in profile["columns"]],
        "summary": summarize_csv(profile),
        "card_file": csv_card_file(profile),
        "profile_file": csv_profile_file(profile),
        "column_roles": {
            column["name"]: describe_column_role(column, descriptions)
            for column in profile["columns"]
        },
    }


def _render_csv_profile(profile: dict[str, Any]) -> list[str]:
    lines = ["## Profiling Details", ""]
    if profile["notes"]:
        lines.extend(["Notes:", *[f"- {note}" for note in profile["notes"]], ""])
    if profile["columns"]:
        lines.extend(["Columns:", *_render_columns(profile["columns"]), ""])
    if profile["head"]:
        lines.extend(["Head sample (first 5 rows):", "```json", json.dumps(profile["head"][:5], indent=2, ensure_ascii=False), "```", ""])
    if profile["tail"]:
        lines.extend(["Tail sample (last 5 rows):", "```json", json.dumps(profile["tail"][-5:], indent=2, ensure_ascii=False), "```", ""])
    return lines


def _render_columns(columns: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for column in columns:
        inferred = ", ".join(f"{name}={count}" for name, count in sorted(column["type_counts"].items())) or "none"
        lines.append(f"- `{column['name']}`: non-empty={column['non_empty_count']}, empty={column['empty_count']}, inferred={inferred}")
        if column.get("numeric_stats"):
            stats = column["numeric_stats"]
            lines.append(f"  numeric stats: min={stats['min']}, max={stats['max']}, mean={stats['mean']}")
        if column.get("top_values"):
            rendered = ", ".join(f"{item['value']} ({item['count']})" for item in column["top_values"])
            lines.append(f"  top values: {rendered}")
    return lines


def _csv_output_stem(profile: dict[str, Any]) -> str:
    relative_path = profile.get("dataset_relative_path")
    source = relative_path if isinstance(relative_path, str) and relative_path else profile["file_name"]
    return Path(source).with_suffix("").as_posix()
