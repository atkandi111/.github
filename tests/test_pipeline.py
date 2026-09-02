#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
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


def load_module(relative: str, name: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot load {relative}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def issue_event(*, owner: str = "atkandi111", author: str | None = None, labels=None, action="opened"):
    return {
        "action": action,
        "sender": {"login": owner},
        "repository": {"full_name": f"{owner}/example"},
        "issue": {
            "number": 12,
            "state": "open",
            "user": {"login": author or owner},
            "title": "Ship the requested change",
            "body": "Untrusted requirements",
            "labels": [{"name": name} for name in (labels or ["implementation"])],
        },
    }


def review_event(*, owner: str = "atkandi111", reviewer: str | None = None, state="changes_requested"):
    head_sha = "c" * 40
    return {
        "action": "submitted",
        "sender": {"login": reviewer or owner},
        "repository": {"full_name": f"{owner}/example"},
        "review": {
            "state": state,
            "user": {"login": reviewer or owner},
            "body": "Please fix this.",
            "commit_id": head_sha,
        },
        "pull_request": {
            "number": 20,
            "state": "open",
            "base": {"ref": "main"},
            "head": {"ref": "issue/12", "sha": head_sha, "repo": {"full_name": f"{owner}/example"}},
        },
    }


def implementation_result(status: str = "implemented") -> dict:
    return {
        "status": status,
        "summary": "Delivered the requested behavior.",
        "question": None,
        "scope": ["Updated the focused implementation."],
        "acceptance_evidence": ["The requested behavior is covered."],
        "documentation": "Updated the relevant workflow documentation.",
        "validation": ["Deterministic CI is authoritative."],
        "review_focus": "Review the focused behavior change.",
        "risk": "Low; limited to the requested path.",
        "rollback": "Revert the merge commit.",
        "followups": [],
    }


def test_pipeline_policy_authorization() -> None:
    policy = load_module("scripts/pipeline_policy.py", "pipeline_policy")
    allowed = policy.authorize_event(issue_event(), "issue_opened", "atkandi111", "main")
    require(allowed == {
        "authorized": True,
        "mode": "new",
        "issue_number": 12,
        "pr_number": 0,
        "branch": "issue/12",
    }, "owner-authored Implementation Issue was not authorized")

    denied = (
        (issue_event(author="someone-else"), "issue_opened", 0),
        (issue_event(labels=["planning"]), "issue_opened", 0),
        (issue_event(labels=["implementation", "planning"]), "issue_opened", 0),
        (issue_event(action="edited"), "issue_opened", 0),
        ({**issue_event(), "sender": {"login": "someone-else"}}, "issue_opened", 0),
        ({**issue_event(labels=["planning"]), "issue": {**issue_event(labels=["planning"])["issue"], "body": "@codex implement this issue"}}, "issue_opened", 0),
    )
    for payload, kind, number in denied:
        require(
            not policy.authorize_event(payload, kind, "atkandi111", "main", number)["authorized"],
            f"invalid Issue event was authorized: {payload}",
        )

    revision = policy.authorize_event(review_event(), "revision_requested", "atkandi111", "main")
    require(revision["authorized"] and revision["issue_number"] == 12, "owner revision was rejected")
    for payload in (
        review_event(reviewer="someone-else"),
        review_event(state="approved"),
        {**review_event(), "review": {**review_event()["review"], "commit_id": "d" * 40}},
        {**review_event(), "pull_request": {**review_event()["pull_request"], "head": {"ref": "feature/x", "repo": {"full_name": "atkandi111/example"}}}},
        {**review_event(), "pull_request": {**review_event()["pull_request"], "head": {"ref": "issue/12", "repo": {"full_name": "someone/fork"}}}},
    ):
        require(
            not policy.authorize_event(payload, "revision_requested", "atkandi111", "main")["authorized"],
            "unauthorized revision was accepted",
        )

    manual = {"sender": {"login": "atkandi111"}, "repository": {"full_name": "atkandi111/example"}}
    require(policy.authorize_event(manual, "manual", "atkandi111", "main", 12)["authorized"], "owner recovery rejected")
    manual["sender"]["login"] = "someone-else"
    require(not policy.authorize_event(manual, "manual", "atkandi111", "main", 12)["authorized"], "foreign recovery accepted")


def test_pipeline_policy_artifacts_and_rendering() -> None:
    policy = load_module("scripts/pipeline_policy.py", "pipeline_policy_artifacts")
    receipt = [[{
        "event": "labeled",
        "label": {"name": "agent:authorized"},
        "actor": {"login": "github-actions[bot]"},
    }]]
    require(policy.has_authorization_receipt(receipt), "trusted authorization receipt rejected")
    receipt[0][0]["actor"]["login"] = "atkandi111"
    require(not policy.has_authorization_receipt(receipt), "human-added later label became authorization")

    result = implementation_result()
    policy.validate_result(result)
    invalid = {**result, "unexpected": True}
    try:
        policy.validate_result(invalid)
    except policy.ContractError:
        pass
    else:
        raise AssertionError("unexpected result fields were accepted")

    patch = b"diff --git a/a b/a\n"
    provenance = {
        "repository": "atkandi111/example",
        "issue_number": 12,
        "mode": "new",
        "start_sha": "a" * 40,
        "run_id": 10,
        "run_attempt": 1,
        "patch_sha256": hashlib.sha256(patch).hexdigest(),
    }
    policy.validate_provenance(
        provenance,
        repository="atkandi111/example",
        issue_number=12,
        mode="new",
        start_sha="a" * 40,
        run_id=10,
        run_attempt=1,
        patch=patch,
    )
    try:
        policy.validate_provenance(
            provenance,
            repository="atkandi111/example",
            issue_number=13,
            mode="new",
            start_sha="a" * 40,
            run_id=10,
            run_attempt=1,
            patch=patch,
        )
    except policy.ContractError:
        pass
    else:
        raise AssertionError("cross-Issue provenance was accepted")

    require(policy.protected_matches([".github/workflows/ci.yml"]), "workflow path was not protected")
    require(policy.protected_matches([".github/ISSUE_TEMPLATE/01-implementation.yml"]), "authorization form was not protected")
    require(policy.protected_matches(["service/AGENTS.md"]), "nested AGENTS.md was not protected")
    require(policy.protected_matches(["scripts/pipeline_policy.py"]), "pipeline policy helper was not protected")
    require(policy.protected_matches(["templates/client/.github/workflows/agent.yml"]), "client pipeline template was not protected")
    require(policy.protected_matches(["terraform/main.tf"], "terraform/**"), "caller protected path ignored")
    require(not policy.protected_matches(["src/app.ts"]), "ordinary product path was protected")

    issue = issue_event()["issue"]
    result["summary"] = (
        "Delivered <!-- hidden --> safely; do not Closes #99, "
        "Fixes https://github.com/atkandi111/example/issues/99, or mention @person."
    )
    brief = policy.render_merge_brief(
        result,
        issue,
        head_sha="b" * 40,
        ci_state="Passed",
        review_state="Automatic review starts when ready.",
        auto_merge_note="Owner approval remains required.",
    )
    require("<!-- hidden -->" not in brief and "&lt;!-- hidden --&gt;" in brief, "Merge Brief did not neutralize HTML")
    require("Closes #99" not in brief and "Fixes https://" not in brief and "@person" not in brief, "model prose retained GitHub side effects")
    require(brief.count("Closes #12") == 1, "renderer did not keep exactly one trusted closing reference")
    for heading in ("Outcome", "Scope delivered", "Acceptance evidence", "Validation", "Agent review", "Review focus", "Risk and rollback"):
        require(f"### {heading}" in brief, f"Merge Brief is missing {heading}")
    require("Closes #12" in brief and "b" * 40 in brief, "Merge Brief linkage/provenance missing")


def test_workflow_trust_boundaries() -> None:
    agent = read(".github/workflows/agent.yml")
    approval = read(".github/workflows/owner-approval.yml")
    caller = read("templates/client/.github/workflows/agent.yml")
    approval_caller = read("templates/client/.github/workflows/owner-approval.yml")

    require("queue: max" in agent and "cancel-in-progress: false" in agent, "no-drop queue configuration missing")
    require("atkandi-issue-pipeline-${{ github.repository }}" in agent, "queue is not repository-scoped")
    require("Validate immutable authorization" in agent and "agent:authorized" in agent, "trusted intake receipt missing")
    require("Isolated Codex implementation" in agent, "isolated implementation job missing")
    implement_block = agent.split("  implement:", 1)[1].split("  publish:", 1)[0]
    require("contents: read" in implement_block and "contents: write" not in implement_block, "implementation can write GitHub contents")
    require("pull-requests: write" not in implement_block and "publisher_private_key" not in implement_block, "implementation can publish")
    require("permission-profile: \":workspace\"" in implement_block and "safety-strategy: drop-sudo" in implement_block, "Codex sandbox boundary missing")
    require("Clean deterministic publisher" in agent and "apply --check" in agent, "clean publisher validation missing")
    require('gsub("@"; "&#64;")' in agent and 'gsub("#"; "&#35;")' in agent, "untrusted handoff prose can trigger GitHub side effects")
    require("actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1" in agent, "publisher App token is not pinned")
    require("permission-administration: read" in agent and "permission-contents: write" in agent, "publisher App permissions drifted")
    require("gh pr create" in agent and "--draft" in agent, "publisher does not create a draft PR")
    merge_lines = [line for line in agent.splitlines() if "gh pr merge" in line]
    require(len(merge_lines) == 1 and "--auto" in merge_lines[0] and "--match-head-commit" in merge_lines[0], "workflow can directly or stale-merge")
    require("required_approving_review_count >= 1" in agent, "auto-merge does not require review protection")
    require("dismiss_stale_reviews == true" in agent, "stale approvals are not rejected")
    require("required_conversation_resolution.enabled == true" in agent, "unresolved conversations can merge")
    require("atkandi/owner-approval" in agent, "owner approval status is not required")
    require("review.commit_id" in approval and "review_sha" in approval, "owner approval is not head-bound")
    require("pull_request.draft" in approval and '[[ "$draft" == false ]]' in approval, "draft approval can satisfy merge status")
    require("$GITHUB_REPOSITORY_OWNER" in approval and "statuses/$review_sha" in approval, "owner approval identity/status missing")
    require("issues:" in caller and "types: [opened]" in caller, "Issue-opened caller missing")
    require("pull_request_review:" in caller and "changes_requested" in caller, "revision caller missing")
    require("PUBLISHER_APP_PRIVATE_KEY" in caller and "OPENAI_API_KEY" in caller, "caller credentials missing")
    require("PUBLISHER_APP_CLIENT_ID is not configured" in agent, "missing publisher identity does not fail closed")
    require("token: ${{ steps.publisher_token.outputs.token }}" in agent, "publication does not use the scoped App token")
    require("AGENT_PIPELINE_ENABLED" in caller and "AGENT_AUTO_MERGE_ENABLED" in caller, "kill switches missing")
    require("live_auto_merge" in agent and "steps.switches.outputs.auto_merge_enabled" in agent, "auto-merge kill switch is not rechecked live")
    require("owner-approval.yml@main" in approval_caller, "owner approval caller is not centralized")
    require("@codex implement" not in agent and "@codex review" not in agent, "workflow triggers native Codex text commands")


def test_issue_and_handoff_contract() -> None:
    implementation = read(".github/ISSUE_TEMPLATE/01-implementation.yml")
    planning = read(".github/ISSUE_TEMPLATE/02-planning.yml")
    brief = read(".github/pull_request_template.md")
    require('labels: ["implementation"]' in implementation, "Implementation form lacks trusted type label")
    require('labels: ["planning"]' in planning, "Planning form lacks trusted type label")
    require("queued automatically" in implementation, "default queue behavior is unclear")
    require("@codex implement" in implementation and "duplicate" in implementation, "duplicate native trigger warning missing")
    require("does not authorize or start Codex" in planning, "planning boundary missing")
    for field in ("Dependencies and likely overlap", "Integration contract revision"):
        require(field in implementation, f"Implementation form is missing {field}")
    for heading in ("Outcome", "Acceptance evidence", "Validation", "Agent review", "Review focus", "Risk and rollback"):
        require(heading in brief, f"account Merge Brief is missing {heading}")


def test_portfolio_status_lifecycle() -> None:
    status = load_module("scripts/portfolio_status.py", "portfolio_status")
    base_issue = {
        "item_id": "issue-1",
        "url": "https://github.com/atkandi111/example/issues/1",
        "kind": "Issue",
        "state": "OPEN",
        "state_reason": None,
        "execution_started": False,
        "execution_in_progress": False,
        "linked_pull_requests": [],
        "current_status": "Todo",
    }
    require(status.desired_status(base_issue) == "Todo", "unstarted Issue not Todo")
    require(status.desired_status({**base_issue, "execution_started": True}) == "In Progress", "claimed Issue not active")
    draft = {"state": "OPEN", "is_draft": True, "review_decision": None, "execution_in_progress": False}
    ready = {**draft, "is_draft": False}
    require(status.desired_status({**base_issue, "linked_pull_requests": [draft]}) == "In Progress", "draft work not active")
    require(status.desired_status({**base_issue, "linked_pull_requests": [ready]}) == "For Review", "ready work not reviewable")
    require(status.desired_status({**base_issue, "execution_in_progress": True, "linked_pull_requests": [ready]}) == "In Progress", "revision not active")
    require(status.desired_status({**base_issue, "linked_pull_requests": [{**ready, "review_decision": "CHANGES_REQUESTED"}]}) == "In Progress", "changes request not active")
    require(status.desired_status({**base_issue, "linked_pull_requests": [{"state": "MERGED", "merged_at": "now"}]}) == "Done", "merge not Done")
    require(status.desired_status({**base_issue, "state": "CLOSED", "state_reason": "COMPLETED"}) == "Done", "completed Issue not Done")
    require(status.desired_status({**base_issue, "state_reason": "REOPENED"}) == "Todo", "reopened unstarted Issue not Todo")

    pr = {
        "item_id": "pr-1",
        "url": "https://github.com/atkandi111/example/pull/1",
        "kind": "PullRequest",
        "state": "OPEN",
        "is_draft": False,
        "review_decision": None,
        "execution_in_progress": False,
        "merged_at": None,
        "current_status": "Todo",
    }
    require(status.desired_status(pr) == "For Review", "ready PR not For Review")
    require(status.desired_status({**pr, "execution_in_progress": True}) == "In Progress", "revising PR not active")
    require(status.desired_status({**pr, "state": "MERGED"}) == "Done", "merged PR not Done")
    update = {**pr, "current_status": "Todo"}
    planned = status.plan_updates([update, update])
    require(len(planned) == 1 and planned[0]["desired"] == "For Review", "duplicate Project update planned")
    require(status.plan_updates([{**update, "current_status": "For Review"}]) == [], "idempotent retry rewrote Status")


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
    require("git diff --no-renames --name-only -z" in ci, "protected comparison is not rename-safe")
    for protected in (
        ".github/ISSUE_TEMPLATE/**",
        ".github/workflows/**",
        ".github/actions/**",
        "**/AGENTS.md",
        "scripts/pipeline_policy.py",
        "templates/client/.github/workflows/**",
    ):
        require(protected in ci, f"verifier path is not protected: {protected}")
    require("/.github/.github/workflows/ci.yml@main" in client, "client CI does not follow the release channel")


def test_action_pins() -> None:
    for path in (ROOT / ".github/workflows").glob("*.yml"):
        for reference in re.findall(r"(?m)^\s*uses:\s+([^\s#]+)", path.read_text()):
            if reference.startswith("./") or reference.startswith("atkandi111/.github/"):
                continue
            require(re.search(r"@[0-9a-f]{40}$", reference) is not None, f"mutable Action reference in {path.name}: {reference}")


def test_installer() -> None:
    with tempfile.TemporaryDirectory() as directory:
        target = pathlib.Path(directory)
        installed = subprocess.run(
            [str(ROOT / "client-setup"), "install", str(target), "example/.github"],
            text=True,
            capture_output=True,
            check=False,
        )
        require(installed.returncode == 0, installed.stderr)
        for relative in (
            ".github/workflows/agent.yml",
            ".github/workflows/owner-approval.yml",
            ".github/workflows/ci.yml",
            ".github/workflows/governance.yml",
        ):
            require((target / relative).is_file(), f"installer omitted {relative}")
        require("example/.github/.github/workflows/agent.yml@main" in (target / ".github/workflows/agent.yml").read_text(), "agent caller release missing")
        require("platform_ref: main" in (target / ".github/workflows/agent.yml").read_text(), "platform helper release missing")
        repeated = subprocess.run(
            [str(ROOT / "client-setup"), "install", str(target), "example/.github"],
            text=True,
            capture_output=True,
            check=False,
        )
        require(repeated.returncode != 0, "installer overwrote existing files")

    with tempfile.TemporaryDirectory() as directory:
        target = pathlib.Path(directory)
        sha = "a" * 40
        installed = subprocess.run(
            [str(ROOT / "client-setup"), "install-canary", str(target), "example/.github", sha],
            text=True,
            capture_output=True,
            check=False,
        )
        require(installed.returncode == 0, installed.stderr)
        caller = (target / ".github/workflows/agent.yml").read_text()
        require(f"agent.yml@{sha}" in caller and f"platform_ref: {sha}" in caller, "canary did not pin matching agent code")

    with tempfile.TemporaryDirectory() as directory:
        target = pathlib.Path(directory)
        onboarded = subprocess.run(
            [str(ROOT / "client-setup"), "onboard", str(target), "example/.github", "atkandi111/demandph-website"],
            text=True,
            capture_output=True,
            check=False,
        )
        require(onboarded.returncode == 0, onboarded.stderr)
        require("client-setup labels" in onboarded.stdout, "onboarding omitted label setup")

    with tempfile.TemporaryDirectory() as directory:
        target = pathlib.Path(directory)
        (target / ".github/ISSUE_TEMPLATE").mkdir(parents=True)
        (target / ".github/ISSUE_TEMPLATE/local.yml").write_text("name: local\n")
        installed = subprocess.run(
            [str(ROOT / "client-setup"), "install", str(target), "example/.github"],
            text=True,
            capture_output=True,
            check=False,
        )
        require(installed.returncode == 0, installed.stderr)
        checked = subprocess.run(
            [str(ROOT / "client-setup"), "check", str(target)],
            text=True,
            capture_output=True,
            check=False,
        )
        require(checked.returncode != 0 and "overrides account defaults" in checked.stderr, "template override was missed")


def test_portfolio_reconciliation_contract() -> None:
    inventory = [line for line in read("config/portfolio-repositories.txt").splitlines() if line and not line.startswith("#")]
    require(inventory == sorted(inventory) and len(inventory) == len(set(inventory)), "portfolio inventory is invalid")
    reconciler = read("scripts/reconcile-portfolio-project")
    workflow = read(".github/workflows/portfolio-project.yml")
    require("schedule:" in workflow and "workflow_dispatch:" in workflow, "Portfolio triggers missing")
    require("PORTFOLIO_PROJECT_TOKEN" in workflow and "contents: read" in workflow, "Project credential boundary drifted")
    require("addProjectV2ItemById" in reconciler and "updateProjectV2ItemFieldValue" in reconciler, "Project reconciliation mutation missing")
    require(reconciler.count("updateProjectV2ItemFieldValue") == 1, "Project status mutation duplicated")
    require("agent:authorized" in reconciler and "agent:in-progress" in reconciler, "Project lifecycle does not mirror pipeline state")
    require("issues/$number/comments" not in reconciler, "obsolete comment authorization remains")
    for forbidden in ("item-delete", "item-archive"):
        require(forbidden not in reconciler, f"Project reconciler may destructively normalize: {forbidden}")
    require("comm -23" in reconciler and "verify --plan" in reconciler, "idempotent reconciliation missing")


def test_documented_operating_contract() -> None:
    corpus = "\n".join(read(path) for path in (
        "README.md",
        "docs/issue-planning.md",
        "docs/security.md",
        "docs/cloud-setup.md",
        "docs/release.md",
        "docs/governance-rollout.md",
        "policy/AGENTS.md",
    ))
    for phrase in (
        "implementation",
        "planning",
        "queue: max",
        "GitHub App",
        "owner approval",
        "automatic Codex review",
        "manual merge",
        "one executable Issue per repository",
    ):
        require(phrase.lower() in corpus.lower(), f"documentation is missing {phrase}")
    require("@codex implement this issue" not in corpus, "obsolete native implementation trigger remains")
    require(len(read("policy/AGENTS.md").encode()) <= 4096, "shared policy exceeds the 4 KiB budget")


def main() -> None:
    tests = (
        test_pipeline_policy_authorization,
        test_pipeline_policy_artifacts_and_rendering,
        test_workflow_trust_boundaries,
        test_issue_and_handoff_contract,
        test_portfolio_status_lifecycle,
        test_missing_project_access,
        test_reusable_ci_boundary,
        test_action_pins,
        test_installer,
        test_portfolio_reconciliation_contract,
        test_documented_operating_contract,
    )
    for test in tests:
        test()
        print(f"ok: {test.__name__}")


if __name__ == "__main__":
    main()
