from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from recruitment_tool.csv_io import CsvInputError, read_csv
from recruitment_tool.overview import build_overview, format_overview


HEADER = "姓名,学号,邮箱,志愿1,志愿2,推荐人\n"


class OverviewTests(unittest.TestCase):
    def write_csv(self, content: str, *, encoding: str = "utf-8-sig") -> Path:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "input.csv"
        path.write_text(content, encoding=encoding, newline="")
        return path

    def test_reads_bom_chinese_and_preserves_leading_zero(self) -> None:
        path = self.write_csv(
            HEADER + "测试甲,00123456,00123456@smbu.edu.cn,项目开发部,,\n"
        )
        data = read_csv(path)
        self.assertEqual(data.rows[0].value_at(data.header_index("学号")), "00123456")

    def test_counts_data_rows_and_whitespace_as_empty(self) -> None:
        path = self.write_csv(
            HEADER
            + "测试甲,001,001@smbu.edu.cn,项目开发部,   ,\n"
            + "测试乙,002,,项目开发部,,推荐人\n"
        )
        data = read_csv(path)
        overview = build_overview(data)
        self.assertEqual(overview.row_count, 2)
        self.assertEqual(overview.empty_counts["邮箱"], 1)
        self.assertEqual(overview.empty_counts["志愿2"], 2)
        self.assertEqual(overview.empty_counts["推荐人"], 1)

    def test_reports_exact_duplicate_groups_and_extra_rows(self) -> None:
        repeated = "测试甲,001,001@smbu.edu.cn,项目开发部,,\n"
        path = self.write_csv(HEADER + repeated * 3)
        data = read_csv(path)
        overview = build_overview(data)
        self.assertTrue(overview.has_exact_duplicates)
        self.assertEqual(overview.duplicate_group_count, 1)
        self.assertEqual(overview.extra_duplicate_row_count, 2)
        self.assertIn("完全重复行：有", format_overview(data, overview))

    def test_header_only_file_has_zero_rows(self) -> None:
        data = read_csv(self.write_csv(HEADER))
        overview = build_overview(data)
        self.assertEqual(overview.row_count, 0)
        self.assertFalse(overview.has_exact_duplicates)

    def test_blank_physical_lines_are_ignored(self) -> None:
        data = read_csv(self.write_csv(HEADER + "\n\n"))
        self.assertEqual(build_overview(data).row_count, 0)

    def test_empty_file_is_fatal(self) -> None:
        with self.assertRaisesRegex(CsvInputError, "缺少表头"):
            read_csv(self.write_csv(""))

    def test_missing_required_header_is_fatal(self) -> None:
        with self.assertRaisesRegex(CsvInputError, "推荐人"):
            read_csv(self.write_csv("姓名,学号,邮箱,志愿1,志愿2\n"))

    def test_short_row_counts_missing_trailing_cells_as_empty(self) -> None:
        data = read_csv(self.write_csv(HEADER + "测试甲,001\n"))
        overview = build_overview(data)
        self.assertEqual(overview.empty_counts["邮箱"], 1)
        self.assertEqual(overview.empty_counts["推荐人"], 1)


if __name__ == "__main__":
    unittest.main()
