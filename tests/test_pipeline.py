#!/usr/bin/env python3
from __future__ import annotations

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
    brief = read("templates/client/.github/pull_request_template.md")
    require("@codex implement this issue" in implementation, "implementation Issue is not the queue action")
    require(
        "type: textarea\n    id: codex-authorization" in implementation,
        "Codex authorization is not a submitted Issue field",
    )
    require("value: \"@codex implement this issue" in implementation, "queue instruction is not prefilled")
    require("one draft pull request" in implementation, "one-Issue/one-PR contract missing")
    require("does not authorize or start Codex" in planning, "planning opt-out boundary missing")
    for heading in ("Outcome", "Acceptance evidence", "Validation", "Review focus", "Risk and rollback"):
        require(heading in brief, f"Merge Brief is missing {heading}")
    require(
        read(".github/ISSUE_TEMPLATE/01-implementation.yml") == implementation,
        "implementation Issue copies drifted",
    )
    require(read(".github/ISSUE_TEMPLATE/02-planning.yml") == planning, "planning Issue copies drifted")
    require(read(".github/pull_request_template.md") == brief, "Merge Brief copies drifted")


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
    require("contents: read" in workflow, "reconciliation workflow must keep repository access read-only")
    require("PORTFOLIO_PROJECT_TOKEN" in workflow, "Project credential contract missing")
    require("addProjectV2ItemById" in reconciler, "reconciler cannot add missing items")
    require("gh project" not in reconciler, "reconciler relies on ambiguous gh project owner resolution")
    require("projectV2(number: $number)" in reconciler, "Project ID is not queried from owner and number")
    for forbidden in ("item-delete", "item-archive", "item-edit"):
        require(forbidden not in reconciler, f"reconciler may modify existing Project data: {forbidden}")
    require("comm -23" in reconciler and "sort -u" in reconciler, "idempotent membership comparison missing")


def main() -> None:
    tests = (
        test_removed_custom_runtime,
        test_issue_and_handoff_contract,
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
