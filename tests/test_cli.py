from __future__ import annotations

import contextlib
import io
import unittest

from recruitment_tool.cli import build_parser, main


class CliTests(unittest.TestCase):
    def test_parser_accepts_input_and_output_directory(self) -> None:
        args = build_parser().parse_args(["input.csv", "--output-dir", "result"])
        self.assertEqual(args.input_csv.name, "input.csv")
        self.assertEqual(args.output_dir.name, "result")

    def test_missing_input_returns_fatal_error(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            exit_code = main(["input.csv", "--output-dir", "result"])
        self.assertEqual(exit_code, 1)


if __name__ == "__main__":
    unittest.main()

