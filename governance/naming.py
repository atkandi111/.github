"""Portfolio naming policy used by the reusable governance workflow."""

from __future__ import annotations

import os
import re
import subprocess
import sys


CONVENTIONAL = re.compile(
    r"^(?:build|chore|ci|docs|feat|fix|perf|refactor|revert|test)"
    r"(?:\([a-z0-9][a-z0-9.-]*\))?!?: [a-z0-9].{0,71}$"
)
HUMAN_BRANCH = re.compile(
    r"^(?:chore|ci|docs|feat|fix|refactor|test)/[a-z0-9]+(?:-[a-z0-9]+)*$"
)
PIPELINE_BRANCH = re.compile(r"^issue/[1-9][0-9]*$")
FORBIDDEN_ISSUE_PREFIX = re.compile(
    r"^(?:\[[^]]+\]\s*|(?:agent|codex|repo|repository|status|priority|task)\s*:\s*)",
    re.IGNORECASE,
)
CONVENTIONAL_ISSUE_PREFIX = re.compile(
    r"^(?:build|chore|ci|docs|feat|fix|perf|refactor|revert|test)(?:\([^)]*\))?!?:\s",
    re.IGNORECASE,
)


def fail(messages: list[str]) -> int:
    for message in messages:
        print(f"::error::{message}")
    return 1


def validate_issue(title: str) -> int:
    errors: list[str] = []
    words = title.split()
    if not title or title != title.strip():
        errors.append("Issue title must not be empty or padded with whitespace")
    if len(title) > 60:
        errors.append("Issue title must be 60 characters or fewer")
    if title.endswith("."):
        errors.append("Issue title must not end with a period")
    if title and title[0].isalpha() and not title[0].isupper():
        errors.append("Issue title must use sentence case")
    if FORBIDDEN_ISSUE_PREFIX.search(title) or CONVENTIONAL_ISSUE_PREFIX.search(title):
        errors.append("Issue title must not include metadata, tool, task, or Conventional Commit prefixes")
    if not 3 <= len(words) <= 8:
        print("::warning::Prefer a concise Issue title of 3-8 words")
    return fail(errors) if errors else 0


def validate_pr(title: str, branch: str, base_ref: str, legacy: set[str], automation: tuple[str, ...]) -> int:
    errors: list[str] = []
    if branch in legacy:
        print(f"::warning::Exact legacy branch exception used: {branch}")
    elif branch.startswith(("agent/", "codex/")):
        errors.append("New agent/ and codex/ branches are forbidden")
    elif not (
        HUMAN_BRANCH.fullmatch(branch)
        or PIPELINE_BRANCH.fullmatch(branch)
        or any(branch.startswith(prefix) and len(branch) > len(prefix) for prefix in automation)
    ):
        errors.append("Branch must use <type>/<short-kebab-scope>, issue/<number>, or an approved automation prefix")
    if not CONVENTIONAL.fullmatch(title):
        errors.append("Pull-request title must be a concise Conventional Commit subject")

    result = subprocess.run(
        ["git", "log", "--format=%s", f"origin/{base_ref}...HEAD"],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode != 0:
        errors.append("Unable to compare proposed commits with the trusted base")
    else:
        for subject in result.stdout.splitlines():
            if not CONVENTIONAL.fullmatch(subject):
                errors.append(f"Commit subject is not Conventional Commit format: {subject!r}")
    return fail(errors) if errors else 0


def main() -> int:
    kind = os.environ.get("RECORD_KIND", "")
    title = os.environ.get("RECORD_TITLE", "")
    if kind == "issue":
        return validate_issue(title)
    if kind != "pull_request":
        return fail(["record_kind must be issue or pull_request"])
    legacy = {value for value in os.environ.get("LEGACY_BRANCHES", "").splitlines() if value}
    automation = tuple(value for value in os.environ.get("AUTOMATION_PREFIXES", "dependabot/").splitlines() if value)
    return validate_pr(title, os.environ.get("HEAD_BRANCH", ""), os.environ.get("BASE_REF", ""), legacy, automation)


if __name__ == "__main__":
    sys.exit(main())
