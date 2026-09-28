from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from recruitment_tool.cli import main
from recruitment_tool.csv_io import read_csv
from recruitment_tool.statistics import (
    build_preference_statistics,
    write_clean_data,
    write_first_preference_summary,
)
from recruitment_tool.validation import validate_rows, write_issue_list


HEADER = "姓名,学号,邮箱,志愿1,志愿2,推荐人,备注\n"


class StatisticsTests(unittest.TestCase):
    def make_input(self, rows: str) -> tuple[Path, Path]:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        root = Path(temp_dir.name)
        source = root / "input.csv"
        source.write_text(HEADER + rows, encoding="utf-8-sig", newline="")
        return source, root / "output"

    def test_statistics_use_only_clean_records(self) -> None:
        source, _ = self.make_input(
            "测试甲,001,001@smbu.edu.cn,项目开发部,,,A\n"
            "测试乙,002,002@smbu.edu.cn,创新创业部,项目开发部,,B\n"
            "问题行,ABC,wrong@example.com,项目开发部,,,C\n"
        )
        data = read_csv(source)
        validation = validate_rows(data)
        stats = build_preference_statistics(data, validation)
        self.assertEqual(stats.first_preference_counts, {"创新创业部": 1, "项目开发部": 1})
        self.assertEqual(stats.one_preference_count, 1)
        self.assertEqual(stats.both_preferences_count, 1)
        self.assertEqual(stats.clean_record_count, len(validation.clean_records))

    def test_writers_keep_bom_header_order_and_extra_columns(self) -> None:
        source, output = self.make_input(
            " 测试甲 ,001,001@SMBU.EDU.CN, 项目开发部 ,,, 保留备注 \n"
        )
        data = read_csv(source)
        validation = validate_rows(data)
        stats = build_preference_statistics(data, validation)
        clean_path = output / "干净数据.csv"
        summary_path = output / "第一志愿汇总.csv"
        issue_path = output / "问题清单.csv"
        write_clean_data(clean_path, data, validation)
        write_first_preference_summary(summary_path, stats)
        write_issue_list(issue_path, data, validation)

        for path in (clean_path, summary_path, issue_path):
            self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))

        with clean_path.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.reader(stream))
        self.assertEqual(rows[0], list(data.headers))
        self.assertEqual(rows[1][-1], "保留备注")
        self.assertEqual(rows[1][2], "001@smbu.edu.cn")

    def test_all_invalid_still_writes_header_only_clean_outputs(self) -> None:
        source, output = self.make_input(
            "问题行,ABC,wrong@example.com,项目开发部,,,A\n"
        )
        exit_code = main([str(source), "--output-dir", str(output)])
        self.assertEqual(exit_code, 0)
        with (output / "干净数据.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as stream:
            self.assertEqual(len(list(csv.reader(stream))), 1)
        with (output / "第一志愿汇总.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as stream:
            self.assertEqual(len(list(csv.reader(stream))), 1)

    def test_end_to_end_outputs_satisfy_count_invariants(self) -> None:
        source, output = self.make_input(
            "测试甲,001,001@smbu.edu.cn,项目开发部,,,A\n"
            "测试乙,002,002@smbu.edu.cn,项目开发部,创新创业部,,B\n"
            "问题行,003,wrong@example.com,创新创业部,,,C\n"
        )
        self.assertEqual(main([str(source), "--output-dir", str(output)]), 0)

        with (output / "问题清单.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as stream:
            issue_count = len(list(csv.DictReader(stream)))
        with (output / "干净数据.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as stream:
            clean_rows = list(csv.DictReader(stream))
        with (output / "第一志愿汇总.csv").open(
            "r", encoding="utf-8-sig", newline=""
        ) as stream:
            summary_total = sum(
                int(row["人数"]) for row in csv.DictReader(stream)
            )

        self.assertEqual(issue_count + len(clean_rows), 3)
        self.assertEqual(summary_total, len(clean_rows))
        self.assertEqual(
            sum(1 for row in clean_rows if row["志愿2"])
            + sum(1 for row in clean_rows if not row["志愿2"]),
            len(clean_rows),
        )


if __name__ == "__main__":
    unittest.main()
