"""Requirement 2: row validation and issue-list export."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import json
from pathlib import Path

from .csv_io import CsvData, SourceRow, write_csv_atomic


REQUIRED_FIELDS = ("姓名", "学号", "邮箱", "志愿1")


@dataclass(frozen=True)
class IssueRecord:
    source: SourceRow
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class CleanRecord:
    line_number: int
    values: tuple[str, ...]


@dataclass(frozen=True)
class ValidationResult:
    issues: tuple[IssueRecord, ...]
    clean_records: tuple[CleanRecord, ...]


def _normalized_values(data: CsvData, row: SourceRow) -> tuple[str, ...]:
    values = tuple(row.value_at(index).strip() for index in range(len(data.headers)))
    email_index = data.header_index("邮箱")
    email = values[email_index]
    if "@" in email:
        local_part, domain = email.rsplit("@", 1)
        values = (
            values[:email_index]
            + (f"{local_part}@{domain.lower()}",)
            + values[email_index + 1 :]
        )
    return values


def validate_rows(data: CsvData) -> ValidationResult:
    student_index = data.header_index("学号")
    student_ids = [row.value_at(student_index).strip() for row in data.rows]
    duplicate_ids = {
        student_id
        for student_id, count in Counter(student_ids).items()
        if student_id and count > 1
    }

    issues: list[IssueRecord] = []
    clean_records: list[CleanRecord] = []
    for row in data.rows:
        reasons: list[str] = []
        if len(row.values) < len(data.headers):
            reasons.append(
                f"列数不足（实际{len(row.values)}列，应为{len(data.headers)}列）"
            )
        elif len(row.values) > len(data.headers):
            reasons.append(
                f"列数过多（实际{len(row.values)}列，应为{len(data.headers)}列）"
            )

        normalized = _normalized_values(data, row)
        value_by_header = dict(zip(data.headers, normalized))
        for field in REQUIRED_FIELDS:
            if not value_by_header[field]:
                reasons.append(f"{field}为空")

        student_id = value_by_header["学号"]
        email = value_by_header["邮箱"]
        if student_id and not student_id.isdigit():
            reasons.append("学号必须为纯数字")
        if student_id and student_id in duplicate_ids:
            reasons.append("学号重复报名")
        if student_id.isdigit() and email:
            expected_email = f"{student_id}@smbu.edu.cn"
            if email != expected_email:
                reasons.append("邮箱与学号不匹配")

        if reasons:
            issues.append(IssueRecord(source=row, reasons=tuple(reasons)))
        else:
            clean_records.append(
                CleanRecord(line_number=row.line_number, values=normalized)
            )

    return ValidationResult(
        issues=tuple(issues), clean_records=tuple(clean_records)
    )


def write_issue_list(
    path: Path, data: CsvData, validation: ValidationResult
) -> None:
    headers = ("原始行号", *data.headers, "问题原因", "原始行内容")
    rows = []
    for issue in validation.issues:
        original_cells = tuple(
            issue.source.value_at(index) for index in range(len(data.headers))
        )
        rows.append(
            (
                str(issue.source.line_number),
                *original_cells,
                "；".join(issue.reasons),
                json.dumps(issue.source.values, ensure_ascii=False),
            )
        )
    write_csv_atomic(path, headers, rows)
