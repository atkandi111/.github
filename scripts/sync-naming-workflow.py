#!/usr/bin/env python3
"""Render the canonical naming validator into the reusable workflow."""

from __future__ import annotations

import argparse
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "governance/naming.py"
WORKFLOW = ROOT / ".github/workflows/governance.yml"
START = "          # BEGIN GENERATED NAMING VALIDATOR\n"
END = "          # END GENERATED NAMING VALIDATOR"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = SOURCE.read_text().rstrip("\n")
    rendered = START + "\n".join(f"          {line}" if line else "" for line in source.splitlines()) + "\n" + END
    workflow = WORKFLOW.read_text()
    start = workflow.find(START)
    end = workflow.find(END, start + len(START))
    if start < 0 or end < 0 or workflow.count(START) != 1 or workflow.count(END) != 1:
        print("workflow must contain exactly one generated validator block", file=sys.stderr)
        return 1
    expected = workflow[:start] + rendered + workflow[end + len(END):]
    if expected == workflow:
        print("naming workflow is synchronized")
        return 0
    if args.check:
        print("naming workflow is not synchronized", file=sys.stderr)
        return 1
    WORKFLOW.write_text(expected)
    print("updated generated naming validator")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
