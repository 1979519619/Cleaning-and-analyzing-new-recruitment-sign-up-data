"""Requirement 3: preference statistics and clean-data export."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .csv_io import CsvData, write_csv_atomic
from .validation import ValidationResult


@dataclass(frozen=True)
class PreferenceStatistics:
    first_preference_counts: dict[str, int]
    both_preferences_count: int
    one_preference_count: int

    @property
    def clean_record_count(self) -> int:
        return self.both_preferences_count + self.one_preference_count


def build_preference_statistics(
    data: CsvData, validation: ValidationResult
) -> PreferenceStatistics:
    first_index = data.header_index("志愿1")
    second_index = data.header_index("志愿2")
    counts = Counter(
        record.values[first_index] for record in validation.clean_records
    )
    both = sum(
        1 for record in validation.clean_records if record.values[second_index]
    )
    one = len(validation.clean_records) - both
    return PreferenceStatistics(
        first_preference_counts=dict(sorted(counts.items())),
        both_preferences_count=both,
        one_preference_count=one,
    )


def write_first_preference_summary(
    path: Path, statistics: PreferenceStatistics
) -> None:
    rows = (
        (preference, str(count))
        for preference, count in statistics.first_preference_counts.items()
    )
    write_csv_atomic(path, ("第一志愿", "人数"), rows)


def write_clean_data(
    path: Path, data: CsvData, validation: ValidationResult
) -> None:
    write_csv_atomic(
        path,
        data.headers,
        (record.values for record in validation.clean_records),
    )
