from __future__ import annotations

import csv
import hashlib
import tempfile
import unittest
from pathlib import Path

from recruitment_tool.csv_io import read_csv
from recruitment_tool.validation import validate_rows, write_issue_list


HEADER = "姓名,学号,邮箱,志愿1,志愿2,推荐人\n"


class ValidationTests(unittest.TestCase):
    def write_input(self, rows: str) -> tuple[Path, tempfile.TemporaryDirectory[str]]:
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        path = Path(temp_dir.name) / "input.csv"
        path.write_text(HEADER + rows, encoding="utf-8-sig", newline="")
        return path, temp_dir

    def test_valid_row_keeps_leading_zero_and_normalizes_domain_case(self) -> None:
        path, _ = self.write_input(
            " 测试甲 ,00123456,00123456@SMBU.EDU.CN, 项目开发部 ,,\n"
        )
        data = read_csv(path)
        result = validate_rows(data)
        self.assertEqual(result.issues, ())
        student_index = data.header_index("学号")
        email_index = data.header_index("邮箱")
        self.assertEqual(result.clean_records[0].values[student_index], "00123456")
        self.assertEqual(
            result.clean_records[0].values[email_index],
            "00123456@smbu.edu.cn",
        )

    def test_combines_required_student_and_email_reasons(self) -> None:
        path, _ = self.write_input(",ABC,wrong@example.com,,,\n")
        result = validate_rows(read_csv(path))
        reasons = result.issues[0].reasons
        self.assertIn("姓名为空", reasons)
        self.assertIn("志愿1为空", reasons)
        self.assertIn("学号必须为纯数字", reasons)

    def test_marks_every_row_in_duplicate_student_group(self) -> None:
        path, _ = self.write_input(
            "测试甲,001,001@smbu.edu.cn,项目开发部,,\n"
            "测试乙,001,001@smbu.edu.cn,创新创业部,,\n"
            "测试丙,001,001@smbu.edu.cn,项目开发部,,\n"
        )
        result = validate_rows(read_csv(path))
        self.assertEqual(len(result.issues), 3)
        self.assertTrue(
            all("学号重复报名" in issue.reasons for issue in result.issues)
        )
        self.assertEqual(result.clean_records, ())

    def test_email_must_match_trimmed_student_number(self) -> None:
        path, _ = self.write_input(
            "测试甲, 001 ,002@smbu.edu.cn,项目开发部,,\n"
        )
        reasons = validate_rows(read_csv(path)).issues[0].reasons
        self.assertIn("邮箱与学号不匹配", reasons)

    def test_short_and_long_rows_are_issues(self) -> None:
        path, _ = self.write_input(
            "短行,001\n"
            "长行,002,002@smbu.edu.cn,项目开发部,,,额外值\n"
        )
        result = validate_rows(read_csv(path))
        self.assertIn("列数不足", result.issues[0].reasons[0])
        self.assertIn("列数过多", result.issues[1].reasons[0])

    def test_issue_export_is_bom_encoded_and_traceable(self) -> None:
        path, temp_dir = self.write_input(
            "短行,001\n"
            "长行,002,002@smbu.edu.cn,项目开发部,,,额外值\n"
        )
        data = read_csv(path)
        result = validate_rows(data)
        output = Path(temp_dir.name) / "out" / "问题清单.csv"
        write_issue_list(output, data, result)
        self.assertTrue(output.read_bytes().startswith(b"\xef\xbb\xbf"))
        with output.open("r", encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(rows[0]["原始行号"], "2")
        self.assertIn("列数不足", rows[0]["问题原因"])
        self.assertIn("额外值", rows[1]["原始行内容"])

    def test_processing_does_not_modify_input_file(self) -> None:
        path, temp_dir = self.write_input(
            "测试甲,001,wrong@example.com,项目开发部,,\n"
        )
        before = hashlib.sha256(path.read_bytes()).hexdigest()
        data = read_csv(path)
        result = validate_rows(data)
        write_issue_list(Path(temp_dir.name) / "问题清单.csv", data, result)
        after = hashlib.sha256(path.read_bytes()).hexdigest()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
