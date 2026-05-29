from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
import re

from ..data import get as get_resource
from ..raw_cache_support import resolve_loom_root


STOP_WORDS = {"a", "an", "and", "for", "how", "in", "is", "of", "the", "to", "what", "which"}
ALIASES = {"capex": ("investment", "capex"), "cost": ("cost", "costs", "investment"), "costs": ("cost", "costs", "investment")}


@dataclass(frozen=True)
class AskCandidate:
    workspace: str
    dataset_path: str
    file_name: str
    relative_path: str
    summary: str
    score: int


def run_ask_query(query: str, workspace_root: Path | str, server_url: str | None = None) -> int:
    candidate = _find_best_candidate(query, Path(workspace_root))
    if candidate is None:
        print("No relevant Loom cards matched this question.")
        print("Scan data into `./loom` first, then try again with a more specific dataset term.")
        return 1

    resource = f"{candidate.workspace}/{candidate.relative_path}"
    try:
        local_path = get_resource(resource, workspace_root=workspace_root, server_url=server_url)
    except Exception as exc:
        print(f"Failed to load the matching raw file: {resource}")
        print(str(exc))
        return 1
    matching_rows = _find_matching_rows(local_path, query)

    print(f"Best match workspace: {candidate.workspace}")
    print(f"Dataset: {candidate.dataset_path}")
    print(f"Raw file: {candidate.relative_path}")
    print(f"Local path: {local_path}")
    print(f"Summary: {candidate.summary}")

    likely_answer = _render_likely_answer(matching_rows)
    if likely_answer:
        print(f"Likely answer: {likely_answer}")

    if not matching_rows:
        print("No exact matching rows were found in the raw file.")
        print("Open the local file above or refine the question with a more specific term.")
        return 0

    print("Matching rows:")
    for row in matching_rows[:5]:
        print(f"- {json.dumps(row, ensure_ascii=False)}")
    return 0


def _find_best_candidate(query: str, workspace_root: Path) -> AskCandidate | None:
    loom_root = resolve_loom_root(workspace_root)
    if not loom_root.exists():
        return None

    terms = _expand_terms(query)
    best: AskCandidate | None = None
    for profile_path in sorted(loom_root.rglob("profile.json")):
        if ".loom" in profile_path.parts or profile_path.parent == loom_root:
            continue
        workspace = profile_path.relative_to(loom_root).parts[0]
        dataset_path = profile_path.parent.relative_to(loom_root / workspace).as_posix()
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        scan_files = {Path(item["topic_relative_path"]).name: item["topic_relative_path"] for item in profile.get("scan_manifest", {}).get("csv_files", [])}
        csv_profiles = {item.get("file_name"): item for item in profile.get("csv_profiles", []) if isinstance(item, dict)}
        for csv_file in profile.get("csv_files", []):
            file_name = str(csv_file.get("file_name", ""))
            relative_path = scan_files.get(file_name)
            if not file_name or not relative_path:
                continue
            text_parts = [
                file_name,
                str(csv_file.get("summary", "")),
                " ".join(str(column) for column in csv_file.get("columns", [])),
                str(profile.get("source", {}).get("summary", "")),
            ]
            csv_profile = csv_profiles.get(file_name, {})
            for column in csv_profile.get("columns", []):
                text_parts.append(str(column.get("name", "")))
                for top_value in column.get("top_values", []):
                    text_parts.append(str(top_value.get("value", "")))
            score = _score_text(" ".join(text_parts), query, terms)
            if score <= 0:
                continue
            candidate = AskCandidate(
                workspace=workspace,
                dataset_path=dataset_path,
                file_name=file_name,
                relative_path=relative_path,
                summary=str(csv_file.get("summary", "")),
                score=score,
            )
            if best is None or candidate.score > best.score:
                best = candidate
    return best


def _find_matching_rows(local_path: Path, query: str) -> list[dict[str, str]]:
    terms = _expand_terms(query)
    scored_rows: list[tuple[int, dict[str, str]]] = []
    with local_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            normalized = {str(key): str(value or "") for key, value in row.items()}
            score = _score_text(" ".join(normalized.values()), query, terms)
            if score > 0:
                scored_rows.append((score, normalized))
    scored_rows.sort(key=lambda item: item[0], reverse=True)
    return [row for _, row in scored_rows[:5]]


def _render_likely_answer(rows: list[dict[str, str]]) -> str | None:
    if len(rows) != 1:
        return None
    row = rows[0]
    for key in ("value", "cost", "capex", "investment"):
        if row.get(key):
            unit = f" {row['unit']}" if row.get("unit") else ""
            label = row.get("technology") or row.get("tech") or row.get("name") or "match"
            parameter = f" ({row['parameter']})" if row.get("parameter") else ""
            return f"{label}{parameter} = {row[key]}{unit}"
    return None


def _score_text(text: str, query: str, terms: tuple[str, ...]) -> int:
    lowered = text.lower()
    score = 0
    if query.lower() in lowered:
        score += 8
    for term in terms:
        if term and term in lowered:
            score += 3 if len(term) > 3 else 1
    return score


def _expand_terms(query: str) -> tuple[str, ...]:
    raw_terms = [term.lower() for term in re.findall(r"[A-Za-z0-9_-]+", query)]
    expanded: list[str] = []
    for term in raw_terms:
        if term in STOP_WORDS:
            continue
        expanded.append(term)
        expanded.extend(ALIASES.get(term, ()))
    return tuple(dict.fromkeys(expanded))
