"""CSV input primitives shared by all processing stages."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


EXPECTED_HEADERS = ("姓名", "学号", "邮箱", "志愿1", "志愿2", "推荐人")


class CsvInputError(ValueError):
    """Raised when an input CSV cannot satisfy the documented contract."""


@dataclass(frozen=True)
class SourceRow:
    """One source data row with its physical CSV line number."""

    line_number: int
    values: tuple[str, ...]

    def value_at(self, index: int) -> str:
        return self.values[index] if index < len(self.values) else ""


@dataclass(frozen=True)
class CsvData:
    headers: tuple[str, ...]
    rows: tuple[SourceRow, ...]

    def header_index(self, name: str) -> int:
        return self.headers.index(name)


def read_csv(path: Path) -> CsvData:
    """Read a UTF-8-with-optional-BOM CSV without modifying it."""

    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        try:
            header_row = next(reader)
        except StopIteration as exc:
            raise CsvInputError("输入 CSV 为空，缺少表头。") from exc

        headers = tuple(value.strip() for value in header_row)
        if not headers or all(not value for value in headers):
            raise CsvInputError("输入 CSV 缺少有效表头。")
        if any(not value for value in headers):
            raise CsvInputError("输入 CSV 存在空表头。")
        if len(set(headers)) != len(headers):
            raise CsvInputError("输入 CSV 存在重复表头。")

        missing = [name for name in EXPECTED_HEADERS if name not in headers]
        if missing:
            raise CsvInputError("输入 CSV 缺少字段：" + "、".join(missing))

        rows = tuple(
            SourceRow(line_number=line_number, values=tuple(values))
            for line_number, values in enumerate(reader, start=2)
            if values
        )
    return CsvData(headers=headers, rows=rows)
