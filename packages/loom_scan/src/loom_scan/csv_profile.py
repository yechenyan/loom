from __future__ import annotations

from collections import Counter, deque
import csv
from dataclasses import dataclass, field
import math
from pathlib import Path
from typing import Any


@dataclass
class NumericStats:
    count: int = 0
    minimum: float | None = None
    maximum: float | None = None
    total: float = 0.0

    def update(self, value: float) -> None:
        self.count += 1
        self.total += value
        if self.minimum is None or value < self.minimum:
            self.minimum = value
        if self.maximum is None or value > self.maximum:
            self.maximum = value

    def to_dict(self) -> dict[str, Any]:
        mean = self.total / self.count if self.count else None
        return {
            "count": self.count,
            "min": self.minimum,
            "max": self.maximum,
            "mean": mean,
        }


@dataclass
class ColumnProfile:
    name: str
    non_empty_count: int = 0
    empty_count: int = 0
    type_counts: Counter[str] = field(default_factory=Counter)
    unique_examples: Counter[str] = field(default_factory=Counter)
    numeric_stats: NumericStats = field(default_factory=NumericStats)

    def update(self, raw_value: str) -> None:
        value = raw_value.strip()
        if not value:
            self.empty_count += 1
            return

        self.non_empty_count += 1
        inferred_type, parsed = _infer_value_type(value)
        self.type_counts[inferred_type] += 1

        if inferred_type == "number" and isinstance(parsed, float):
            self.numeric_stats.update(parsed)
        elif len(self.unique_examples) < 20 or value in self.unique_examples:
            self.unique_examples[value] += 1

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "name": self.name,
            "non_empty_count": self.non_empty_count,
            "empty_count": self.empty_count,
            "type_counts": dict(self.type_counts),
        }

        if self.numeric_stats.count:
            result["numeric_stats"] = self.numeric_stats.to_dict()

        if self.unique_examples:
            result["top_values"] = [
                {"value": value, "count": count}
                for value, count in self.unique_examples.most_common(10)
            ]

        return result


def profile_csv(csv_path: Path, sample_size: int = 10) -> dict[str, Any]:
    file_size = csv_path.stat().st_size
    if file_size == 0:
        return {
            "file_name": csv_path.name,
            "file_size_bytes": 0,
            "dialect": {"delimiter": ","},
            "columns": [],
            "row_count": 0,
            "head": [],
            "tail": [],
            "notes": ["File is empty."],
        }

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        sample = handle.read(4096)
        handle.seek(0)
        dialect = _sniff_dialect(sample)
        reader = csv.DictReader(handle, dialect=dialect)

        fieldnames = reader.fieldnames or []
        columns = [ColumnProfile(name=name) for name in fieldnames]
        head_rows: list[dict[str, str]] = []
        tail_rows: deque[dict[str, str]] = deque(maxlen=sample_size)
        row_count = 0

        for row in reader:
            normalized_row = {name: row.get(name, "") or "" for name in fieldnames}
            if len(head_rows) < sample_size:
                head_rows.append(normalized_row)
            tail_rows.append(normalized_row)
            row_count += 1

            for column in columns:
                column.update(normalized_row.get(column.name, ""))

    notes: list[str] = []
    if not fieldnames:
        notes.append("CSV file does not contain a header row.")
    if row_count == 0:
        notes.append("CSV file contains a header but no data rows.")

    return {
        "file_name": csv_path.name,
        "file_size_bytes": file_size,
        "dialect": {"delimiter": dialect.delimiter},
        "columns": [column.to_dict() for column in columns],
        "row_count": row_count,
        "head": head_rows,
        "tail": list(tail_rows),
        "notes": notes,
    }


def _sniff_dialect(sample: str) -> csv.Dialect:
    if not sample.strip():
        return csv.get_dialect("excel")

    try:
        return csv.Sniffer().sniff(sample, delimiters=",\t;|")
    except csv.Error:
        return csv.get_dialect("excel")


def _infer_value_type(value: str) -> tuple[str, Any]:
    lowered = value.lower()
    if lowered in {"true", "false", "yes", "no"}:
        return "boolean", lowered in {"true", "yes"}

    try:
        number = float(value)
    except ValueError:
        return "string", value

    if math.isfinite(number):
        return "number", number

    return "string", value
