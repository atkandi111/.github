#!/usr/bin/env python3
"""Read-only audit for registered repositories, governance, and Projects."""

from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import pathlib
import subprocess
import sys
from collections.abc import Callable


ROOT = pathlib.Path(__file__).resolve().parents[1]
Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]
REQUIRED_PROTECTION = {
    "required_pull_request_reviews",
    "block_force_pushes",
    "block_deletions",
}


def gh(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["gh", *args], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def detail(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stderr or result.stdout).strip()


def parse_object(result: subprocess.CompletedProcess[str], label: str) -> tuple[dict[str, object] | None, str | None]:
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        return None, f"{label} returned invalid JSON: {error}"
    if not isinstance(value, dict):
        return None, f"{label} must return a JSON object"
    return value, None


def disabled(value: object) -> bool:
    return value is False or isinstance(value, dict) and value.get("enabled") is False


def at_least_one(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 1


def classic_controls(data: dict[str, object]) -> tuple[set[str], set[str]]:
    controls: set[str] = set()
    contexts: set[str] = set()
    checks = data.get("required_status_checks")
    if isinstance(checks, dict):
        raw_checks = checks.get("checks")
        if isinstance(raw_checks, list):
            contexts.update(str(item.get("context")) for item in raw_checks if isinstance(item, dict) and item.get("context"))
        raw_contexts = checks.get("contexts")
        if isinstance(raw_contexts, list):
            contexts.update(str(item) for item in raw_contexts if isinstance(item, str) and item)
    reviews = data.get("required_pull_request_reviews")
    if isinstance(reviews, dict) and at_least_one(reviews.get("required_approving_review_count")):
        controls.add("required_pull_request_reviews")
    if disabled(data.get("allow_force_pushes")):
        controls.add("block_force_pushes")
    if disabled(data.get("allow_deletions")):
        controls.add("block_deletions")
    return controls, contexts


def ruleset_controls(data: list[object]) -> tuple[set[str], set[str]]:
    controls: set[str] = set()
    contexts: set[str] = set()
    for item in data:
        if not isinstance(item, dict):
            continue
        rule_type = item.get("type")
        parameters = item.get("parameters")
        if rule_type == "required_status_checks" and isinstance(parameters, dict):
            raw_checks = parameters.get("required_status_checks")
            if isinstance(raw_checks, list):
                contexts.update(str(check.get("context")) for check in raw_checks if isinstance(check, dict) and check.get("context"))
        elif rule_type == "pull_request" and isinstance(parameters, dict) and at_least_one(parameters.get("required_approving_review_count")):
            controls.add("required_pull_request_reviews")
        elif rule_type == "non_fast_forward":
            controls.add("block_force_pushes")
        elif rule_type == "deletion":
            controls.add("block_deletions")
    return controls, contexts


def audit_protection(name: str, branch: str, required_contexts: set[str], run: Runner) -> dict[str, object]:
    classic = run(["api", f"repos/{name}/branches/{branch}/protection"])
    rules = run(["api", f"repos/{name}/rules/branches/{branch}"])
    controls: set[str] = set()
    contexts: set[str] = set()
    sources: list[str] = []
    errors: list[str] = []

    if classic.returncode == 0:
        data, error = parse_object(classic, "classic branch protection")
        if error:
            errors.append(error)
        elif data is not None:
            classic_control_set, classic_context_set = classic_controls(data)
            controls.update(classic_control_set)
            contexts.update(classic_context_set)
            sources.append("classic")
    elif "HTTP 404" not in detail(classic) and "Branch not protected" not in detail(classic):
        errors.append(detail(classic) or "classic branch protection query failed")

    if rules.returncode == 0:
        try:
            data = json.loads(rules.stdout)
        except json.JSONDecodeError as error:
            errors.append(f"effective rules query returned invalid JSON: {error}")
        else:
            if isinstance(data, list):
                ruleset_control_set, ruleset_context_set = ruleset_controls(data)
                controls.update(ruleset_control_set)
                contexts.update(ruleset_context_set)
                sources.append("rulesets")
            else:
                errors.append("effective rules query must return a JSON list")
    elif "HTTP 404" not in detail(rules):
        errors.append(detail(rules) or "effective rules query failed")

    missing = sorted(REQUIRED_PROTECTION - controls)
    missing.extend(f"required_status_check:{context}" for context in sorted(required_contexts - contexts))
    if errors and (not sources or missing):
        return {"status": "human_input", "controls": sorted(controls), "status_checks": sorted(contexts), "missing": missing, "detail": "\n".join(errors)}
    return {
        "status": "protected" if not missing else "missing",
        "sources": sources,
        "controls": sorted(controls),
        "status_checks": sorted(contexts),
        "missing": missing,
        **({"detail": "\n".join(errors)} if errors else {}),
    }


def read_managed_file(
    name: str, branch: str, contract: dict[str, object], run: Runner
) -> tuple[str, str | None]:
    path = str(contract.get("path", ""))
    response = run(["api", f"repos/{name}/contents/{path}?ref={branch}"])
    if response.returncode != 0:
        message = detail(response)
        return ("missing", path) if "HTTP 404" in message else ("human_input", message or f"failed to read {path}")
    data, error = parse_object(response, f"managed file {path}")
    if error or data is None:
        return "human_input", error
    if data.get("type") != "file" or data.get("encoding") != "base64":
        return "drift", f"{path}: expected a regular file"
    encoded = data.get("content")
    if not isinstance(encoded, str):
        return "human_input", f"{path}: API response omitted base64 content"
    try:
        content = base64.b64decode("".join(encoded.split()), validate=True)
        text = content.decode("utf-8")
    except (binascii.Error, ValueError, UnicodeDecodeError) as error:
        return "human_input", f"{path}: unreadable content: {error}"
    if not content:
        return "drift", f"{path}: managed file is empty"

    kind = contract.get("kind")
    if kind == "overlay":
        maximum = int(contract.get("max_bytes") or 0)
        if maximum <= 0 or len(content) > maximum:
            return "drift", f"{path}: overlay is {len(content)} bytes; maximum is {maximum}"
    elif kind == "contains":
        markers = contract.get("all")
        if not isinstance(markers, list) or not markers or not all(isinstance(marker, str) and marker for marker in markers):
            return "human_input", f"{path}: invalid contains contract"
        missing = [marker for marker in markers if marker not in text]
        if missing:
            return "drift", f"{path}: missing contract marker(s): {missing}"
    elif kind == "sha256":
        expected = contract.get("digest")
        actual = "sha256:" + hashlib.sha256(content).hexdigest()
        if expected != actual:
            return "drift", f"{path}: expected {expected}, found {actual}"
    else:
        return "human_input", f"{path}: unknown managed-file contract {kind!r}"
    return "pass", None


def audit_repository(entry: dict[str, object], contracts: list[dict[str, object]], run: Runner = gh) -> dict[str, object]:
    name = str(entry["name"])
    expected_default = str(entry["default_branch"])
    result: dict[str, object] = {"repository": name, "role": entry["role"], "findings": []}
    findings: list[dict[str, str]] = result["findings"]  # type: ignore[assignment]

    metadata = run(["api", f"repos/{name}"])
    if metadata.returncode != 0:
        findings.append({"level": "human_input", "check": "repository_access", "detail": detail(metadata)})
        result["status"] = "human_input"
        return result
    repository, error = parse_object(metadata, "repository metadata")
    if error or repository is None:
        findings.append({"level": "human_input", "check": "repository_metadata", "detail": error or "invalid metadata"})
        result["status"] = "human_input"
        return result
    if repository.get("default_branch") != expected_default:
        findings.append({"level": "drift", "check": "default_branch", "detail": f"expected {expected_default}, found {repository.get('default_branch')}"})
    if repository.get("archived"):
        findings.append({"level": "human_input", "check": "archived", "detail": "registered repository is archived"})

    merge_settings = {
        "allow_squash_merge": repository.get("allow_squash_merge"),
        "allow_merge_commit": repository.get("allow_merge_commit"),
        "allow_rebase_merge": repository.get("allow_rebase_merge"),
        "squash_merge_commit_title": repository.get("squash_merge_commit_title"),
    }
    result["merge_settings"] = merge_settings
    if (
        merge_settings["allow_squash_merge"] is not True
        or merge_settings["allow_merge_commit"] is not False
        or merge_settings["allow_rebase_merge"] is not False
        or merge_settings["squash_merge_commit_title"] != "PR_TITLE"
    ):
        findings.append({"level": "drift", "check": "merge_strategy", "detail": "only squash merging with PR_TITLE is allowed"})

    required_contexts = entry.get("required_status_checks")
    if not isinstance(required_contexts, list) or not required_contexts or not all(isinstance(item, str) and item for item in required_contexts):
        findings.append({"level": "human_input", "check": "protection_contract", "detail": "required_status_checks must be a non-empty string list"})
        context_set: set[str] = set()
    else:
        context_set = set(required_contexts)
    protection = audit_protection(name, expected_default, context_set, run)
    result["branch_protection"] = protection
    if protection["status"] != "protected":
        level = "human_input" if protection["status"] == "human_input" else "drift"
        findings.append({"level": level, "check": "branch_protection", "detail": str(protection.get("detail") or protection.get("missing"))})

    files: dict[str, str] = {}
    for contract in contracts:
        path = str(contract.get("path", ""))
        status, message = read_managed_file(name, expected_default, contract, run)
        files[path] = status
        if status != "pass":
            level = "human_input" if status == "human_input" else "drift"
            findings.append({"level": level, "check": "managed_file", "detail": message or path})
    result["managed_files"] = files

    levels = {finding["level"] for finding in findings}
    result["status"] = "human_input" if "human_input" in levels else "drift" if "drift" in levels else "pass"
    return result


def audit_project(project: dict[str, object], run: Runner = gh) -> dict[str, object]:
    owner = str(project["owner"])
    number = str(project["number"])
    view = run(["project", "view", number, "--owner", owner, "--format", "json"])
    fields = run(["project", "field-list", number, "--owner", owner, "--format", "json"])
    if view.returncode != 0 or fields.returncode != 0:
        message = "\n".join(value for value in (detail(view), detail(fields)) if value)
        return {"status": "human_input", "detail": message}
    try:
        data = json.loads(view.stdout)
        field_data = json.loads(fields.stdout)
    except json.JSONDecodeError as error:
        return {"status": "human_input", "detail": f"Project query returned invalid JSON: {error}"}
    if not isinstance(data, dict) or not isinstance(field_data, dict) or not isinstance(field_data.get("fields"), list):
        return {"status": "human_input", "detail": "Project query returned an unexpected shape"}

    findings: list[str] = []
    seen_ids: set[str] = set()
    actual_fields = field_data["fields"]
    expected_fields = project.get("fields")
    if not isinstance(expected_fields, dict):
        return {"status": "human_input", "detail": "Project field contracts are missing"}
    for name, contract in expected_fields.items():
        matches = [field for field in actual_fields if isinstance(field, dict) and field.get("name") == name]
        if len(matches) != 1:
            findings.append(f"{name}: expected exactly one field, found {len(matches)}")
            continue
        field = matches[0]
        field_id = field.get("id")
        if not isinstance(field_id, str) or not field_id or field_id in seen_ids:
            findings.append(f"{name}: field identity is missing or duplicated")
        else:
            seen_ids.add(field_id)
        if not isinstance(contract, dict) or field.get("type") != contract.get("type"):
            findings.append(f"{name}: field type drift")
        expected_options = set(contract.get("options", [])) if isinstance(contract, dict) else set()
        options = field.get("options")
        actual_options = {str(option.get("name")) for option in options if isinstance(option, dict)} if isinstance(options, list) else set()
        if actual_options != expected_options:
            findings.append(f"{name}: option drift")
    if data.get("title") != project["name"]:
        findings.append(f"title: expected {project['name']}, found {data.get('title')}")
    return {"status": "drift" if findings else "pass", "title": data.get("title"), "field_drift": findings}


def audit_exception(exception: dict[str, object], run: Runner = gh) -> dict[str, object]:
    result = {"repository": exception.get("repository"), "kind": exception.get("kind")}
    if not isinstance(exception.get("owner"), str) or not exception.get("owner"):
        return {**result, "status": "drift", "detail": "exception owner is required"}
    expiry = exception.get("expires")
    if not isinstance(expiry, dict) or expiry.get("kind") != "pull_request_closed":
        return {**result, "status": "drift", "detail": "machine-readable pull_request_closed expiry is required"}
    repository = expiry.get("repository")
    number = expiry.get("number")
    if not isinstance(repository, str) or not isinstance(number, int):
        return {**result, "status": "drift", "detail": "expiry repository and PR number are required"}
    if repository != exception.get("repository"):
        return {**result, "status": "drift", "detail": "expiry repository must match the excepted repository"}
    response = run(["api", f"repos/{repository}/pulls/{number}"])
    if response.returncode != 0:
        return {**result, "status": "human_input", "detail": detail(response) or "exception expiry query failed"}
    data, error = parse_object(response, "exception expiry")
    if error or data is None:
        return {**result, "status": "human_input", "detail": error or "invalid exception expiry"}
    if data.get("state") != "open":
        return {**result, "status": "drift", "detail": f"exception expired when {repository}#{number} closed"}
    if exception.get("kind") == "legacy_branch":
        head = data.get("head")
        if not isinstance(head, dict) or head.get("ref") != exception.get("value"):
            return {**result, "status": "drift", "detail": "expiry PR head does not match the excepted legacy branch"}
        head_repository = head.get("repo")
        if not isinstance(head_repository, dict) or head_repository.get("full_name") != exception.get("repository"):
            return {**result, "status": "drift", "detail": "expiry PR head repository does not match the exception"}
    return {**result, "status": "pass", "detail": f"active until {repository}#{number} closes"}


def unmanaged_repository(entry: dict[str, object], exceptions: list[dict[str, object]]) -> dict[str, object]:
    name = str(entry["name"])
    matches = [item for item in exceptions if item.get("repository") == name and item.get("kind") == "unmanaged_repository"]
    if len(matches) == 1 and matches[0].get("status") == "pass":
        return {"repository": name, "role": entry["role"], "managed": False, "status": "pass", "findings": [{"level": "exception", "check": "unmanaged_repository", "detail": str(matches[0]["detail"])}]}
    level = "human_input" if any(item.get("status") == "human_input" for item in matches) else "drift"
    return {"repository": name, "role": entry["role"], "managed": False, "status": level, "findings": [{"level": level, "check": "unmanaged_repository", "detail": "unmanaged repositories require one active, owned, expiring exception"}]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=pathlib.Path, default=ROOT / "governance/repositories.json")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text())
    exception_reports = [audit_exception(item) for item in inventory.get("exceptions", [])]
    repositories = []
    for entry in inventory["repositories"]:
        if entry.get("managed") is True:
            repositories.append(audit_repository(entry, inventory["required_files"][entry["role"]]))
        else:
            repositories.append(unmanaged_repository(entry, exception_reports))
    project = audit_project(inventory["project"])
    report = {"repositories": repositories, "project": project, "exceptions": exception_reports}
    statuses = {item["status"] for item in repositories + exception_reports} | {project["status"]}
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
