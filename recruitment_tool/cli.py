"""Command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Sequence

from .csv_io import CsvInputError, read_csv
from .overview import build_overview, format_overview


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
    except (CsvInputError, OSError, UnicodeError) as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    print(format_overview(data, overview))
    print("校验与导出将在后续需求 PR 中实现。")
    return 0

