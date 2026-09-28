"""Command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence


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
    print(f"输入文件：{args.input_csv}")
    print(f"输出目录：{args.output_dir}")
    print("项目骨架已就绪，业务功能将在后续需求 PR 中实现。")
    return 0

