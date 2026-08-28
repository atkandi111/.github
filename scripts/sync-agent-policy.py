#!/usr/bin/env python3
"""Render the canonical central policy into the reusable agent workflow."""

from __future__ import annotations

import argparse
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "governance/AGENTS.md"
WORKFLOW = ROOT / ".github/workflows/agent.yml"
CI_WORKFLOW = ROOT / ".github/workflows/ci.yml"
START = "            <central_policy>\n"
END = "            </central_policy>"
MAX_POLICY_BYTES = 4 * 1024
BYTE_MARKER = '          CENTRAL_POLICY_BYTES: "'


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
    ci_workflow = CI_WORKFLOW.read_text()
    marker_start = ci_workflow.find(BYTE_MARKER)
    if marker_start < 0 or ci_workflow.find(BYTE_MARKER, marker_start + 1) >= 0:
        print("CI workflow must contain exactly one central-policy byte marker", file=sys.stderr)
        return 1
    value_start = marker_start + len(BYTE_MARKER)
    value_end = ci_workflow.find('"', value_start)
    if value_end < 0:
        print("CI workflow central-policy byte marker is malformed", file=sys.stderr)
        return 1
    expected_ci = ci_workflow[:value_start] + str(len(source_bytes)) + ci_workflow[value_end:]

    if expected == workflow and expected_ci == ci_workflow:
        print("central policy is synchronized")
        return 0
    if args.check:
        print("central policy is not synchronized; run scripts/sync-agent-policy.py", file=sys.stderr)
        return 1
    WORKFLOW.write_text(expected)
    CI_WORKFLOW.write_text(expected_ci)
    print("updated generated central policy block and CI byte marker")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
