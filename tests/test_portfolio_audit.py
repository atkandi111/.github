#!/usr/bin/env python3
"""Behavioral allow-and-deny fixtures for the read-only portfolio audit."""

from __future__ import annotations

import base64
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


def encoded_file(content: str) -> str:
    return json.dumps({"type": "file", "encoding": "base64", "content": base64.b64encode(content.encode()).decode()})


def valid_protection() -> dict[str, object]:
    return {
        "required_status_checks": {"checks": [{"context": "ci"}]},
        "required_pull_request_reviews": {"required_approving_review_count": 1},
        "allow_force_pushes": {"enabled": False},
        "allow_deletions": {"enabled": False},
    }


def fake_repository_runner(
    *,
    metadata_changes: dict[str, object] | None = None,
    classic: dict[str, object] | None = None,
    rules: list[object] | None = None,
    file_content: str = "required marker\n",
    file_error: str = "",
):
    metadata = {
        "default_branch": "main",
        "archived": False,
        "allow_squash_merge": True,
        "allow_merge_commit": False,
        "allow_rebase_merge": False,
        "squash_merge_commit_title": "PR_TITLE",
    }
    metadata.update(metadata_changes or {})

    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        endpoint = args[1] if args and args[0] == "api" else ""
        if endpoint == "repos/example/client":
            return completed(0, json.dumps(metadata))
        if endpoint.endswith("/protection"):
            return completed(0, json.dumps(valid_protection() if classic is None else classic))
        if "/rules/branches/" in endpoint:
            return completed(0, json.dumps([] if rules is None else rules))
        if "/contents/" in endpoint:
            if file_error:
                return completed(1, stderr=file_error)
            return completed(0, encoded_file(file_content))
        raise AssertionError(args)

    return run


def project_runner(fields: list[dict[str, object]]):
    def run(args: list[str]) -> subprocess.CompletedProcess[str]:
        if args[:2] == ["project", "view"]:
            return completed(0, json.dumps({"title": "Portfolio"}))
        if args[:2] == ["project", "field-list"]:
            return completed(0, json.dumps({"fields": fields}))
        raise AssertionError(args)

    return run


def main() -> None:
    entry = {"name": "example/client", "role": "client", "default_branch": "main", "managed": True}
    contracts = [{"path": "AGENTS.md", "kind": "contains", "all": ["required marker"]}]

    passed = AUDIT.audit_repository(entry, contracts, fake_repository_runner())
    assert passed["status"] == "pass"

    weak_protection = AUDIT.audit_repository(entry, contracts, fake_repository_runner(classic={}))
    assert weak_protection["status"] == "drift"
    assert weak_protection["branch_protection"]["missing"] == sorted(AUDIT.REQUIRED_PROTECTION)

    bypass_merge = AUDIT.audit_repository(
        entry, contracts, fake_repository_runner(metadata_changes={"allow_rebase_merge": True})
    )
    assert bypass_merge["status"] == "drift"
    assert any(item["check"] == "merge_strategy" for item in bypass_merge["findings"])

    stale = AUDIT.audit_repository(entry, contracts, fake_repository_runner(file_content="obsolete\n"))
    assert stale["status"] == "drift" and stale["managed_files"]["AGENTS.md"] == "drift"
    missing = AUDIT.audit_repository(entry, contracts, fake_repository_runner(file_error="HTTP 404"))
    assert missing["status"] == "drift" and missing["managed_files"]["AGENTS.md"] == "missing"
    inaccessible = AUDIT.audit_repository(entry, contracts, fake_repository_runner(file_error="HTTP 403 rate limit"))
    assert inaccessible["status"] == "human_input"

    def plan_blocked(args: list[str]) -> subprocess.CompletedProcess[str]:
        endpoint = args[1] if args and args[0] == "api" else ""
        if endpoint == "repos/example/client":
            return fake_repository_runner()(args)
        if endpoint.endswith("/protection") or "/rules/branches/" in endpoint:
            return completed(1, stderr="Upgrade to GitHub Pro or make this repository public (HTTP 403)")
        if "/contents/" in endpoint:
            return completed(0, encoded_file("required marker\n"))
        raise AssertionError(args)

    blocked = AUDIT.audit_repository(entry, contracts, plan_blocked)
    assert blocked["status"] == "human_input" and blocked["branch_protection"]["status"] == "human_input"

    rules = [
        {"type": "required_status_checks", "parameters": {"required_status_checks": [{"context": "ci"}]}},
        {"type": "pull_request", "parameters": {"required_approving_review_count": 1}},
        {"type": "non_fast_forward"},
        {"type": "deletion"},
    ]
    rules_only = AUDIT.audit_repository(entry, contracts, fake_repository_runner(classic={}, rules=rules))
    assert rules_only["status"] == "pass", "effective rulesets may supply every required control"

    project = {
        "owner": "example",
        "number": 1,
        "name": "Portfolio",
        "fields": {
            "Status": {"type": "ProjectV2SingleSelectField", "options": ["Todo", "Done"]},
        },
    }
    status_field = {
        "id": "PVTF_status",
        "name": "Status",
        "type": "ProjectV2SingleSelectField",
        "options": [{"name": "Todo"}, {"name": "Done"}],
    }
    assert AUDIT.audit_project(project, project_runner([status_field]))["status"] == "pass"
    duplicate_fields = [status_field, {**status_field, "id": "PVTF_other"}]
    duplicate = AUDIT.audit_project(project, project_runner(duplicate_fields))
    assert duplicate["status"] == "drift" and "expected exactly one" in duplicate["field_drift"][0]
    wrong_type = AUDIT.audit_project(project, project_runner([{**status_field, "type": "ProjectV2Field"}]))
    assert wrong_type["status"] == "drift"

    exception = {
        "repository": "example/client",
        "kind": "legacy_branch",
        "owner": "maintainer",
        "expires": {"kind": "pull_request_closed", "repository": "example/client", "number": 55},
    }

    def exception_state(state: str):
        return lambda args: completed(0, json.dumps({"state": state}))

    active = AUDIT.audit_exception(exception, exception_state("open"))
    expired = AUDIT.audit_exception(exception, exception_state("closed"))
    assert active["status"] == "pass" and expired["status"] == "drift"
    malformed = AUDIT.audit_exception({**exception, "expires": "PR #55 closes"}, exception_state("open"))
    assert malformed["status"] == "drift"

    unmanaged = {**entry, "managed": False}
    visible = AUDIT.unmanaged_repository(unmanaged, [])
    assert visible["status"] == "drift", "unmanaged repositories must never be silently dropped"
    exemption = {**active, "kind": "unmanaged_repository"}
    assert AUDIT.unmanaged_repository(unmanaged, [exemption])["status"] == "pass"

    inventory = json.loads((ROOT / "governance/repositories.json").read_text())
    assert len(inventory["repositories"]) == 5
    assert inventory["exceptions"][0]["expires"]["number"] == 55
    assert all(isinstance(item, dict) and item.get("kind") for items in inventory["required_files"].values() for item in items)
    print("ok: portfolio audit")


if __name__ == "__main__":
    main()
