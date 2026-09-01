#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
import pathlib
import re
import subprocess
import tempfile


ROOT = pathlib.Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_removed_custom_runtime() -> None:
    require(not (ROOT / ".github/workflows/agent.yml").exists(), "central agent runner still exists")
    require(not (ROOT / "templates/client/.github/workflows/agent.yml").exists(), "client agent caller still exists")
    corpus = "\n".join(
        path.read_text(errors="replace")
        for path in ROOT.rglob("*")
        if path.is_file()
        and ".git" not in path.parts
        and "tests" not in path.parts
        and path.name != "client-setup"
        and path != ROOT / "docs/transition.md"
    )
    for obsolete in ("OPENAI_API_KEY", "AGENT_PIPELINE_ENABLED", "status_pending", "issue/<number>-attempt"):
        require(obsolete not in corpus, f"obsolete runtime contract remains: {obsolete}")


def test_issue_and_handoff_contract() -> None:
    implementation = read("templates/client/.github/ISSUE_TEMPLATE/01-implementation.yml")
    planning = read("templates/client/.github/ISSUE_TEMPLATE/02-planning.yml")
    planning_guide = read("docs/issue-planning.md")
    policy = read("policy/AGENTS.md")
    brief = read("templates/client/.github/pull_request_template.md")
    trigger = "@codex implement this issue in this repository. Open one draft pull request and complete its Merge Brief."
    require(trigger in implementation, "implementation Issue does not show the exact owner trigger")
    require(trigger in policy, "shared policy drifted from the supported owner trigger")
    require(
        "id: codex-authorization" not in implementation,
        "Issue form still submits an unsupported Issue-body trigger",
    )
    require("Publishing records a reviewed contract but does not start Codex" in implementation, "publish boundary missing")
    require("one draft pull request" in implementation, "one-Issue/one-PR contract missing")
    require("Create PR" in implementation, "Create PR handoff missing from implementation form")
    require("docs/issue-planning.md" in implementation, "implementation Issue does not link planning guidance")
    require("does not authorize or start Codex" in planning, "planning opt-out boundary missing")
    require("docs/issue-planning.md" in planning, "planning Issue does not link planning guidance")
    for contract in (
        "one cohesive, reviewable repository outcome",
        "one executable Issue per repository",
        "non-executable planning subissues",
    ):
        require(contract in planning_guide, f"Issue planning guide is missing: {contract}")
        require(contract in policy, f"shared policy is missing Issue-planning context: {contract}")
    readme = read("README.md")
    cloud_setup = read("docs/cloud-setup.md")
    require("owner's exact top-level" in readme, "README queue action drifted")
    require("publishing the Issue alone does not start Codex" in cloud_setup, "canary trigger evidence missing")
    require("Create PR" in readme and "Create PR" in cloud_setup, "Create PR handoff missing")
    for heading in ("Outcome", "Acceptance evidence", "Validation", "Review focus", "Risk and rollback"):
        require(heading in brief, f"Merge Brief is missing {heading}")
    require(
        read(".github/ISSUE_TEMPLATE/01-implementation.yml") == implementation,
        "implementation Issue copies drifted",
    )
    require(read(".github/ISSUE_TEMPLATE/02-planning.yml") == planning, "planning Issue copies drifted")
    require(read(".github/pull_request_template.md") == brief, "Merge Brief copies drifted")


def load_status_module():
    path = ROOT / "scripts/portfolio_status.py"
    spec = importlib.util.spec_from_file_location("portfolio_status", path)
    require(spec is not None and spec.loader is not None, "status planner cannot be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_portfolio_status_lifecycle() -> None:
    status = load_status_module()
    trigger = status.TRIGGER_COMMENT
    allowed = {
        "body": trigger,
        "user": {"login": "atkandi111"},
        "created_at": "2026-09-01T00:00:00Z",
        "updated_at": "2026-09-01T00:00:00Z",
    }
    require(status.has_valid_owner_trigger([[allowed]], "atkandi111"), "exact owner trigger was rejected")
    require(
        status.has_valid_owner_trigger([[allowed, allowed]], "atkandi111"),
        "duplicate delivery changed the trigger decision",
    )
    denied = (
        {**allowed, "user": {"login": "someone-else"}},
        {**allowed, "updated_at": "2026-09-01T00:01:00Z"},
        {**allowed, "body": f"> {trigger}"},
        {**allowed, "body": f"{trigger}\n"},
        {**allowed, "body": "@codex implement something similar"},
    )
    for comment in denied:
        require(not status.has_valid_owner_trigger([[comment]], "atkandi111"), f"invalid trigger accepted: {comment}")

    base_issue = {
        "item_id": "issue-1",
        "url": "https://github.com/atkandi111/example/issues/1",
        "kind": "Issue",
        "state": "OPEN",
        "state_reason": None,
        "owner_triggered": False,
        "linked_pull_requests": [],
        "current_status": "Todo",
        "body": trigger,
    }
    require(status.desired_status(base_issue) == "Todo", "Issue-body text changed Status")
    require(status.desired_status({**base_issue, "owner_triggered": True}) == "In Progress", "queued Issue not active")
    require(
        status.desired_status(
            {**base_issue, "linked_pull_requests": [{"state": "OPEN", "is_draft": True, "review_decision": None}]}
        )
        == "In Progress",
        "draft linked PR not active",
    )
    require(
        status.desired_status(
            {**base_issue, "linked_pull_requests": [{"state": "OPEN", "is_draft": False, "review_decision": None}]}
        )
        == "For Review",
        "ready linked PR not reviewable",
    )
    require(
        status.desired_status(
            {
                **base_issue,
                "linked_pull_requests": [
                    {"state": "OPEN", "is_draft": False, "review_decision": "CHANGES_REQUESTED"}
                ],
            }
        )
        == "In Progress",
        "changes requested did not resume implementation",
    )
    require(
        status.desired_status({**base_issue, "linked_pull_requests": [{"state": "MERGED", "merged_at": "now"}]})
        == "Done",
        "merged linked PR did not complete Issue",
    )
    require(
        status.desired_status(
            {
                **base_issue,
                "state_reason": "REOPENED",
                "linked_pull_requests": [{"state": "MERGED", "merged_at": "now"}],
            }
        )
        == "Todo",
        "historical merged PR overrode reopened Issue",
    )
    require(
        status.desired_status({**base_issue, "state": "CLOSED", "state_reason": "COMPLETED"}) == "Done",
        "completed Issue not Done",
    )
    require(
        status.desired_status({**base_issue, "state_reason": "REOPENED"}) == "Todo",
        "reopened unstarted Issue not Todo",
    )

    pull_request = {
        "item_id": "pr-1",
        "url": "https://github.com/atkandi111/example/pull/1",
        "kind": "PullRequest",
        "state": "OPEN",
        "is_draft": True,
        "review_decision": None,
        "merged_at": None,
        "current_status": "Todo",
    }
    require(status.desired_status(pull_request) == "In Progress", "draft PR not In Progress")
    require(status.desired_status({**pull_request, "is_draft": False}) == "For Review", "ready PR not For Review")
    require(
        status.desired_status({**pull_request, "is_draft": False, "review_decision": "CHANGES_REQUESTED"})
        == "In Progress",
        "changes-requested PR not In Progress",
    )
    require(status.desired_status({**pull_request, "state": "MERGED"}) == "Done", "merged PR not Done")

    update = {**pull_request, "current_status": "Todo"}
    planned = status.plan_updates([update, update])
    require(len(planned) == 1 and planned[0]["desired"] == "In Progress", "duplicate event planned twice")
    require(status.plan_updates([{**update, "current_status": "In Progress"}]) == [], "idempotent retry rewrote Status")
    require(status.verify_updates(planned, [{**update, "current_status": "In Progress"}]) == [], "verification failed")


def test_missing_project_access() -> None:
    with tempfile.TemporaryDirectory() as directory:
        fake_gh = pathlib.Path(directory) / "gh"
        fake_gh.write_text("#!/bin/sh\nexit 1\n")
        fake_gh.chmod(0o755)
        result = subprocess.run(
            [str(ROOT / "scripts/reconcile-portfolio-project"), "audit"],
            text=True,
            capture_output=True,
            check=False,
            env={**os.environ, "PATH": f"{directory}:{os.environ['PATH']}"},
        )
        require(result.returncode != 0, "missing Project access did not fail")
        require("unable to read the Portfolio Project" in result.stderr, "missing-access action is unclear")


def test_reusable_ci_boundary() -> None:
    ci = read(".github/workflows/ci.yml")
    client = read("templates/client/.github/workflows/ci.yml")
    require("permissions:\n      contents: read" in ci, "CI must be read-only")
    require("secrets:" not in ci and "id-token: write" not in ci, "CI must be credential-free")
    require("git diff --no-renames --name-only -z" in ci, "protected-path comparison is not rename-safe")
    require(".github/workflows/**" in ci and ".github/actions/**" in ci, "verifier paths are not protected")
    require(
        'patterns = [\n              ".github/workflows"' in ci,
        "immutable protected paths can be replaced by a caller",
    )
    require("dev-platform/.github/workflows/ci.yml@main" in client, "client does not follow the main release channel")
    require("workflow_dispatch" not in client, "obsolete custom dispatch remains")


def test_action_pins() -> None:
    for relative in (
        ".github/workflows/ci.yml",
        ".github/workflows/platform-checks.yml",
        ".github/workflows/portfolio-project.yml",
    ):
        for reference in re.findall(r"uses:\s+([^\s#]+)", read(relative)):
            if reference.startswith("./"):
                continue
            require(re.search(r"@[0-9a-f]{40}$", reference) is not None, f"mutable Action reference: {reference}")


def test_installer() -> None:
    with tempfile.TemporaryDirectory() as directory:
        target = pathlib.Path(directory)
        installed = subprocess.run(
            [str(ROOT / "client-setup"), "install", str(target), "example/dev-platform"],
            text=True,
            capture_output=True,
            check=False,
        )
        require(installed.returncode == 0, installed.stderr)
        require(not (target / ".github/workflows/agent.yml").exists(), "installer added custom agent caller")
        require(
            "example/dev-platform/.github/workflows/ci.yml@main"
            in (target / ".github/workflows/ci.yml").read_text(),
            "installer did not set the release channel",
        )
        repeated = subprocess.run(
            [str(ROOT / "client-setup"), "install", str(target), "example/dev-platform"],
            text=True,
            capture_output=True,
            check=False,
        )
        require(repeated.returncode != 0, "installer overwrote existing files")

    with tempfile.TemporaryDirectory() as directory:
        target = pathlib.Path(directory)
        onboarded = subprocess.run(
            [
                str(ROOT / "client-setup"),
                "onboard",
                str(target),
                "example/dev-platform",
                "atkandi111/demandph-website",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        require(onboarded.returncode == 0, onboarded.stderr)

    with tempfile.TemporaryDirectory() as directory:
        target = pathlib.Path(directory)
        unregistered = subprocess.run(
            [
                str(ROOT / "client-setup"),
                "onboard",
                str(target),
                "example/dev-platform",
                "example/unregistered-client",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        require(unregistered.returncode != 0, "onboarding accepted an unregistered client")


def test_portfolio_reconciliation_contract() -> None:
    inventory = [
        line
        for line in read("config/portfolio-repositories.txt").splitlines()
        if line and not line.startswith("#")
    ]
    require(inventory == sorted(inventory), "portfolio inventory is not alphabetized")
    require(len(inventory) == len(set(inventory)), "portfolio inventory contains duplicates")
    for repository in (
        "atkandi111/Mahjongtale",
        "atkandi111/demandph-website",
        "atkandi111/dev-platform",
        "atkandi111/infrastructure",
        "atkandi111/rotary-binan-website",
    ):
        require(repository in inventory, f"portfolio inventory is missing {repository}")

    workflow = read(".github/workflows/portfolio-project.yml")
    reconciler = read("scripts/reconcile-portfolio-project")
    require("schedule:" in workflow and "workflow_dispatch:" in workflow, "reconciliation triggers missing")
    require('cron: "7,22,37,52 * * * *"' in workflow, "Status reconciliation is not scheduled every 15 minutes")
    require("contents: read" in workflow, "reconciliation workflow must keep repository access read-only")
    require("PORTFOLIO_PROJECT_TOKEN" in workflow, "Project credential contract missing")
    require("addProjectV2ItemById" in reconciler, "reconciler cannot add missing items")
    require("updateProjectV2ItemFieldValue" in reconciler, "reconciler cannot mirror lifecycle Status")
    require(reconciler.count("updateProjectV2ItemFieldValue") == 1, "Status mutation may be replayed")
    require("gh project" not in reconciler, "reconciler relies on ambiguous gh project owner resolution")
    require("projectV2(number: $number)" in reconciler, "Project ID is not queried from owner and number")
    for forbidden in ("item-delete", "item-archive"):
        require(forbidden not in reconciler, f"reconciler may modify existing Project data: {forbidden}")
    require("comm -23" in reconciler and "sort -u" in reconciler, "idempotent membership comparison missing")
    require("for attempt in 1 2 3 4 5" in reconciler, "eventual-consistency verification retry missing")
    require(reconciler.count("addProjectV2ItemById") == 1, "Project mutation may be replayed during verification")
    require("verify --plan" in reconciler, "Status updates are not verified read-only")
    require("'For Review'" in reconciler, "For Review status contract missing")


def main() -> None:
    tests = (
        test_removed_custom_runtime,
        test_issue_and_handoff_contract,
        test_portfolio_status_lifecycle,
        test_missing_project_access,
        test_reusable_ci_boundary,
        test_action_pins,
        test_installer,
        test_portfolio_reconciliation_contract,
    )
    for test in tests:
        test()
        print(f"ok: {test.__name__}")


if __name__ == "__main__":
    main()
