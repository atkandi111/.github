#!/usr/bin/env python3
"""Render the canonical central policy into the reusable agent workflow."""

from __future__ import annotations

import argparse
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "governance/AGENTS.md"
WORKFLOW = ROOT / ".github/workflows/agent.yml"
START = "            <central_policy>\n"
END = "            </central_policy>"
MAX_POLICY_BYTES = 4 * 1024


def rendered_block(source: str) -> str:
    body = "".join(f"            {line}\n" if line else "\n" for line in source.rstrip("\n").splitlines())
    return START + body + END


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail instead of updating drift")
    args = parser.parse_args()

    source_bytes = SOURCE.read_bytes()
    if len(source_bytes) > MAX_POLICY_BYTES:
        print(f"central policy exceeds {MAX_POLICY_BYTES} bytes", file=sys.stderr)
        return 1
    source = source_bytes.decode("utf-8")
    if "\r" in source or not source.endswith("\n"):
        print("central policy must be UTF-8 with LF endings and one trailing newline", file=sys.stderr)
        return 1

    workflow = WORKFLOW.read_text()
    start = workflow.find(START)
    end = workflow.find(END, start + len(START))
    if start < 0 or end < 0 or workflow.find(START, start + 1) >= 0 or workflow.find(END, end + 1) >= 0:
        print("workflow must contain exactly one central-policy block", file=sys.stderr)
        return 1

    expected = workflow[:start] + rendered_block(source) + workflow[end + len(END):]
    if expected == workflow:
        print("central policy is synchronized")
        return 0
    if args.check:
        print("central policy is not synchronized; run scripts/sync-agent-policy.py", file=sys.stderr)
        return 1
    WORKFLOW.write_text(expected)
    print("updated generated central policy block")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
