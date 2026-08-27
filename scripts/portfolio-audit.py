#!/usr/bin/env python3
"""Read-only audit for registered portfolio repositories and Project access."""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from collections.abc import Callable


ROOT = pathlib.Path(__file__).resolve().parents[1]
Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]


def gh(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def classify_protection(result: subprocess.CompletedProcess[str]) -> tuple[str, str | None]:
    detail = (result.stderr or result.stdout).strip()
    if result.returncode == 0:
        return "protected", None
    if "Upgrade to GitHub Pro or make this repository public" in detail:
        return "plan_blocked", detail
    if "HTTP 404" in detail or "Branch not protected" in detail:
        return "missing", detail
    return "unknown", detail or "branch protection query failed"


def audit_repository(entry: dict[str, object], required_files: list[str], run: Runner = gh) -> dict[str, object]:
    name = str(entry["name"])
    expected_default = str(entry["default_branch"])
    result: dict[str, object] = {"repository": name, "role": entry["role"], "findings": []}
    findings: list[dict[str, str]] = result["findings"]  # type: ignore[assignment]

    metadata = run(["api", f"repos/{name}"])
    if metadata.returncode != 0:
        findings.append({"level": "human_input", "check": "repository_access", "detail": (metadata.stderr or metadata.stdout).strip()})
        result["status"] = "human_input"
        return result
    try:
        repository = json.loads(metadata.stdout)
    except json.JSONDecodeError as error:
        findings.append({"level": "human_input", "check": "repository_metadata", "detail": str(error)})
        result["status"] = "human_input"
        return result
    if repository.get("default_branch") != expected_default:
        findings.append({"level": "drift", "check": "default_branch", "detail": f"expected {expected_default}, found {repository.get('default_branch')}"})
    if repository.get("archived"):
        findings.append({"level": "human_input", "check": "archived", "detail": "registered repository is archived"})
    result["merge_settings"] = {
        "allow_squash_merge": repository.get("allow_squash_merge"),
        "squash_merge_commit_title": repository.get("squash_merge_commit_title"),
    }
    if not repository.get("allow_squash_merge") or repository.get("squash_merge_commit_title") != "PR_TITLE":
        findings.append({"level": "drift", "check": "merge_strategy", "detail": "squash merging must use the PR title"})

    protection = run(["api", f"repos/{name}/branches/{expected_default}/protection"])
    protection_status, detail = classify_protection(protection)
    result["branch_protection"] = protection_status
    if protection_status != "protected":
        level = "human_input" if protection_status in {"plan_blocked", "unknown"} else "drift"
        findings.append({"level": level, "check": "branch_protection", "detail": detail or protection_status})

    files: dict[str, bool] = {}
    for path in required_files:
        present = run(["api", f"repos/{name}/contents/{path}?ref={expected_default}"]).returncode == 0
        files[path] = present
        if not present:
            findings.append({"level": "drift", "check": "required_file", "detail": path})
    result["required_files"] = files

    levels = {finding["level"] for finding in findings}
    result["status"] = "human_input" if "human_input" in levels else "drift" if "drift" in levels else "pass"
    return result


def audit_project(project: dict[str, object], run: Runner = gh) -> dict[str, object]:
    owner = str(project["owner"])
    number = str(project["number"])
    view = run(["project", "view", number, "--owner", owner, "--format", "json"])
    fields = run(["project", "field-list", number, "--owner", owner, "--format", "json"])
    if view.returncode != 0 or fields.returncode != 0:
        detail = "\n".join(value for value in ((view.stderr or view.stdout).strip(), (fields.stderr or fields.stdout).strip()) if value)
        return {"status": "human_input", "detail": detail}
    data = json.loads(view.stdout)
    field_data = json.loads(fields.stdout)
    expected = {"Status": {"Todo", "In Progress", "Review", "Done"}, "Priority": {"P0", "P1", "P2", "P3"}, "Waiting On": {"Me", "Client"}}
    actual: dict[str, set[str]] = {}
    for field in field_data.get("fields", []):
        actual[str(field.get("name"))] = {str(option.get("name")) for option in field.get("options", [])}
    findings = [name for name, options in expected.items() if actual.get(name) != options]
    status = "drift" if data.get("title") != project["name"] or findings else "pass"
    return {"status": status, "title": data.get("title"), "field_drift": findings}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=pathlib.Path, default=ROOT / "governance/repositories.json")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text())
    repositories = [
        audit_repository(entry, inventory["required_files"][entry["role"]])
        for entry in inventory["repositories"]
        if entry.get("managed")
    ]
    project = audit_project(inventory["project"])
    report = {"repositories": repositories, "project": project, "exceptions": inventory.get("exceptions", [])}
    statuses = {item["status"] for item in repositories} | {project["status"]}
    report["status"] = "human_input" if "human_input" in statuses else "drift" if "drift" in statuses else "pass"
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Portfolio audit: {report['status']}")
        for item in repositories:
            print(f"- {item['repository']}: {item['status']}")
        print(f"- Project: {project['status']}")
        if report["status"] == "human_input":
            print("HUMAN INPUT REQUIRED: inspect the JSON report for exact access or plan blockers.")
    return 2 if report["status"] == "human_input" else 1 if report["status"] == "drift" else 0


if __name__ == "__main__":
    raise SystemExit(main())
