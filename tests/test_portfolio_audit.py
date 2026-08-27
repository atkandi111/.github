#!/usr/bin/env python3
"""Behavioral fixtures for the read-only portfolio audit."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess


ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("portfolio_audit", ROOT / "scripts/portfolio-audit.py")
assert SPEC and SPEC.loader
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


def completed(code: int, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], code, stdout, stderr)


def fake_runner(protected: bool = True, missing_file: str = "", plan_blocked: bool = False):
    metadata = json.dumps({
        "default_branch": "main",
        "archived": False,
        "allow_squash_merge": True,
        "squash_merge_commit_title": "PR_TITLE",
    })

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        endpoint = args[1] if args and args[0] == "api" else ""
        if endpoint == "repos/example/client":
            return completed(0, metadata)
        if endpoint.endswith("/protection"):
            if plan_blocked:
                return completed(1, stderr="Upgrade to GitHub Pro or make this repository public to enable this feature. (HTTP 403)")
            return completed(0 if protected else 1, stderr="Branch not protected (HTTP 404)")
        if "/contents/" in endpoint:
            path_endpoint = endpoint.split("?", 1)[0]
            return completed(1 if missing_file and path_endpoint.endswith(missing_file) else 0, "{}", "HTTP 404")
        raise AssertionError(args)

    return run


def main() -> None:
    entry = {"name": "example/client", "role": "client", "default_branch": "main"}
    passed = AUDIT.audit_repository(entry, ["AGENTS.md"], fake_runner())
    assert passed["status"] == "pass"
    drift = AUDIT.audit_repository(entry, ["AGENTS.md"], fake_runner(missing_file="AGENTS.md"))
    assert drift["status"] == "drift"
    blocked = AUDIT.audit_repository(entry, ["AGENTS.md"], fake_runner(plan_blocked=True))
    assert blocked["status"] == "human_input" and blocked["branch_protection"] == "plan_blocked"
    inventory = json.loads((ROOT / "governance/repositories.json").read_text())
    assert len(inventory["repositories"]) == 5
    assert inventory["exceptions"][0]["value"] == "agent/chore-lightweight-change-management"
    print("ok: portfolio audit")


if __name__ == "__main__":
    main()
