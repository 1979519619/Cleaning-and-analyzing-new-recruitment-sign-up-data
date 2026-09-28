"""Command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from .csv_io import CsvInputError, read_csv
from .overview import build_overview, format_overview
from .statistics import (
    build_preference_statistics,
    write_clean_data,
    write_first_preference_summary,
)
from .validation import validate_rows, write_issue_list


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="清洗并统计项目开发部招新报名 CSV。",
    )
    parser.add_argument("input_csv", type=Path, help="输入 CSV 文件路径")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="输出目录，默认为 ./output",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data = read_csv(args.input_csv)
        overview = build_overview(data)
        validation = validate_rows(data)
        statistics = build_preference_statistics(data, validation)
        issue_path = args.output_dir / "问题清单.csv"
        summary_path = args.output_dir / "第一志愿汇总.csv"
        clean_path = args.output_dir / "干净数据.csv"
        write_issue_list(issue_path, data, validation)
        write_first_preference_summary(summary_path, statistics)
        write_clean_data(clean_path, data, validation)
    except (CsvInputError, OSError, UnicodeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print(format_overview(data, overview))
    print(f"问题记录数：{len(validation.issues)}")
    print(f"干净记录数：{len(validation.clean_records)}")
    print(f"两个志愿都填写：{statistics.both_preferences_count}")
    print(f"只填写一个志愿：{statistics.one_preference_count}")
    print(f"问题清单：{issue_path}")
    print(f"第一志愿汇总：{summary_path}")
    print(f"干净数据：{clean_path}")
    return 0

