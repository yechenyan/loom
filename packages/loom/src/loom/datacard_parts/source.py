from __future__ import annotations

import re
from typing import Any


_COLUMN_HINTS = {
    "technology": "Technology, asset, or entity that the row is describing.",
    "parameter": "Metric or parameter name recorded for the technology in this row.",
    "value": "Primary numeric value recorded for the row.",
    "unit": "Measurement unit for the associated value.",
    "source": "Source or provenance for the value in this row.",
    "further description": "Free-form qualifier, assumption note, or explanatory context for the row.",
    "currency year": "Currency basis year used for money-denominated values.",
    "financial case": "Financial assumption case applied to the row, such as market or R&D.",
    "scenario": "Scenario or pathway label that distinguishes row variants.",
    "date": "Date or timestamp associated with the observation.",
    "year": "Year associated with the observation or assumption.",
    "id": "Identifier for the entity represented by the row.",
    "name": "Human-readable name for the entity represented by the row.",
}


def render_column_list(profile: dict[str, Any]) -> str:
    return "none" if not profile["columns"] else ", ".join(f"`{column['name']}`" for column in profile["columns"])


def render_column_role_list(profile: dict[str, Any], loom_text: str) -> list[str]:
    descriptions = extract_column_descriptions(loom_text)
    return [f"- `{column['name']}`: {describe_column_role(column, descriptions)}" for column in profile["columns"]]


def render_column_role_summary(profile: dict[str, Any], loom_text: str, limit: int = 4) -> str:
    if not profile["columns"]:
        return "No columns were detected."
    descriptions = extract_column_descriptions(loom_text)
    parts = [
        f"`{column['name']}` = {describe_column_role(column, descriptions)}"
        for column in profile["columns"][:limit]
    ]
    remaining = len(profile["columns"]) - limit
    if remaining > 0:
        parts.append(f"{remaining} more columns are explained in the card")
    return "; ".join(parts) + "."


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


def extract_column_descriptions(loom_text: str) -> dict[str, str]:
    descriptions: dict[str, str] = {}
    in_columns = False
    for raw_line in loom_text.splitlines():
        stripped = raw_line.strip()
        lowered = stripped.lower()
        if not stripped:
            continue
        if lowered in {"columns:", "## columns", "# columns"}:
            in_columns = True
            continue
        if not in_columns:
            continue
        if stripped.startswith("#"):
            break
        candidate = stripped[1:].strip() if stripped.startswith("-") else stripped
        match = re.match(r"`?(?P<name>[^`:]+?)`?\s*:\s*(?P<desc>.+)", candidate)
        if match is None:
            if stripped.startswith("-"):
                continue
            break
        descriptions[_normalize_column_key(match.group("name"))] = match.group("desc").strip()
    return descriptions


def describe_column_role(column: dict[str, Any], descriptions: dict[str, str]) -> str:
    explicit = descriptions.get(_normalize_column_key(column["name"]))
    if explicit:
        return explicit
    return _fallback_column_role(column)


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


def _fallback_column_role(column: dict[str, Any]) -> str:
    key = _normalize_column_key(column["name"])
    if key in _COLUMN_HINTS:
        return _COLUMN_HINTS[key]
    if "description" in key or "note" in key:
        return "Free-form descriptive text or qualifier for the row."
    if "source" in key or "reference" in key:
        return "Source or reference attached to the row."
    if "unit" in key:
        return "Measurement unit associated with another value field."
    if "cost" in key or "price" in key:
        return "Numeric cost or price field recorded for the row."
    if "year" in key:
        return "Year field used to qualify the row or its values."
    if column.get("numeric_stats"):
        return "Numeric measure recorded for each row."
    if column["type_counts"].get("string"):
        return "Categorical text field used to label, group, or filter rows."
    return "Field carried through directly from the raw CSV."


def _normalize_column_key(name: str) -> str:
    return " ".join(name.lower().replace("_", " ").replace("-", " ").split())
