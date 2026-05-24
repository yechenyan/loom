from __future__ import annotations

import re
from typing import Any


def render_column_list(profile: dict[str, Any]) -> str:
    return "none" if not profile["columns"] else ", ".join(f"`{column['name']}`" for column in profile["columns"])


def summarize_csv(profile: dict[str, Any]) -> str:
    columns = [column["name"] for column in profile["columns"]]
    if not columns:
        return "No columns were detected in this file."
    lead = ", ".join(f"`{name}`" for name in columns[:4])
    if {"technology", "parameter", "value"}.issubset(columns):
        return f"This table looks like a technology parameter matrix with one row per technology and parameter combination. Key fields include {lead}."
    if {"date", "value"}.issubset(columns):
        return f"This table looks like a time series keyed by {lead}."
    if {"id", "name"}.issubset(columns):
        return f"This table looks like an entity list keyed by {lead}."
    return f"This table appears to describe records organized around {lead}."


def describe_row_layout(profile: dict[str, Any]) -> str:
    columns = [column["name"] for column in profile["columns"]]
    if not columns:
        return "No row pattern could be inferred because no columns were detected."
    if {"technology", "parameter", "value"}.issubset(columns):
        return "Rows appear grouped by `technology`, with repeated `parameter` records describing different metrics for each technology."
    if {"date", "value"}.issubset(columns):
        return "Rows likely progress along `date`, with one measurement record per timestamp."
    if {"id", "name"}.issubset(columns):
        return "Rows likely list one entity per record, keyed by `id` and described by `name`."
    dimensions = [column["name"] for column in profile["columns"] if column["type_counts"].get("string") and column["non_empty_count"] > 0][:3]
    return f"Rows appear organized around the categorical fields {', '.join(f'`{name}`' for name in dimensions)}." if dimensions else "No clear row ordering pattern could be inferred from the sampled records."


def extract_source_info(loom_text: str) -> dict[str, str]:
    source_url = summary = license_text = notes = ""
    for paragraph in [part.strip() for part in loom_text.split("\n\n") if part.strip()]:
        lower = paragraph.lower()
        if lower.startswith("source:"):
            source_url = paragraph.split(":", 1)[1].strip()
        elif not summary and "licence" not in lower and "license" not in lower:
            summary = " ".join(paragraph.splitlines()).strip()
        elif lower.startswith("licence") or lower.startswith("license"):
            license_text = " ".join(paragraph.splitlines()).strip()
        elif not notes:
            notes = " ".join(paragraph.splitlines()).strip()
    return {"url": source_url, "summary": summary, "license": license_text, "notes": notes}


def collect_source_sites(csv_profiles: list[dict[str, Any]]) -> list[str]:
    counts: dict[str, int] = {}
    for profile in csv_profiles:
        for column in profile["columns"]:
            if column["name"] != "source":
                continue
            for item in column.get("top_values", []):
                for site in _extract_urls(item["value"]):
                    counts[site] = counts.get(site, 0) + item["count"]
    return [site for site, _ in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:5]]


def _extract_urls(text: str) -> list[str]:
    seen: list[str] = []
    for match in re.findall(r"https?://\S+", text):
        cleaned = match.rstrip("`.;:>)\"]}'")
        if cleaned not in seen:
            seen.append(cleaned)
    return seen
