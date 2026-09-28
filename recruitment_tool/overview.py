"""Requirement 1: input overview statistics."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from .csv_io import CsvData


@dataclass(frozen=True)
class Overview:
    row_count: int
    empty_counts: dict[str, int]
    duplicate_group_count: int
    extra_duplicate_row_count: int

    @property
    def has_exact_duplicates(self) -> bool:
        return self.duplicate_group_count > 0


def build_overview(data: CsvData) -> Overview:
    empty_counts = {
        header: sum(
            1
            for row in data.rows
            if not row.value_at(column_index).strip()
        )
        for column_index, header in enumerate(data.headers)
    }
    row_frequencies = Counter(row.values for row in data.rows)
    duplicate_sizes = [count for count in row_frequencies.values() if count > 1]
    return Overview(
        row_count=len(data.rows),
        empty_counts=empty_counts,
        duplicate_group_count=len(duplicate_sizes),
        extra_duplicate_row_count=sum(count - 1 for count in duplicate_sizes),
    )


def format_overview(data: CsvData, overview: Overview) -> str:
    empty_lines = "\n".join(
        f"  - {header}：{overview.empty_counts[header]}"
        for header in data.headers
    )
    duplicate_text = "有" if overview.has_exact_duplicates else "没有"
    return (
        f"数据行数（不含表头）：{overview.row_count}\n"
        f"各列空值数：\n{empty_lines}\n"
        f"完全重复行：{duplicate_text}\n"
        f"完全重复组数：{overview.duplicate_group_count}\n"
        f"额外重复行数：{overview.extra_duplicate_row_count}"
    )

