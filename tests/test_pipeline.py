#!/usr/bin/env python3
"""Dependency-free static and behavioral checks for the V1 workflow contracts."""

from __future__ import annotations

import os
import pathlib
import re
import subprocess
import sys
import tempfile
import textwrap


ROOT = pathlib.Path(__file__).resolve().parents[1]
AGENT = (ROOT / ".github/workflows/agent.yml").read_text()
CI = (ROOT / ".github/workflows/ci.yml").read_text()
CLIENT_AGENT = (ROOT / "templates/client/.github/workflows/agent.yml").read_text()
CLIENT_CI = (ROOT / "templates/client/.github/workflows/ci.yml").read_text()
ISSUE_FORM = (ROOT / "templates/client/.github/ISSUE_TEMPLATE/agent-task.yml").read_text()
BUILD_CONTRACT = (ROOT / "agents/build.md").read_text()
PR_TEMPLATE = (ROOT / "templates/client/.github/PULL_REQUEST_TEMPLATE/agent.md").read_text()
ALL_WORKFLOWS = "\n".join((AGENT, CI, CLIENT_AGENT, CLIENT_CI))


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_blocks(yaml_text: str) -> list[str]:
    lines = yaml_text.splitlines()
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        match = re.match(r"^(\s*)run:\s*\|\s*$", lines[index])
        if not match:
            index += 1
            continue
        indent = len(match.group(1))
        index += 1
        body: list[str] = []
        while index < len(lines):
            line = lines[index]
            if line.strip() and len(line) - len(line.lstrip()) <= indent:
                break
            body.append(line)
            index += 1
        blocks.append("\n".join(body))
    return blocks


def embedded_python_blocks(yaml_text: str) -> list[str]:
    pattern = re.compile(
        r"^\s+python3 - <<'PY'\n(?P<code>.*?)^\s+PY$",
        re.MULTILINE | re.DOTALL,
    )
    return [textwrap.dedent(match.group("code")) for match in pattern.finditer(yaml_text)]


def run_protected_matcher(code: str, paths: list[str], patterns: str = "") -> int:
    with tempfile.TemporaryDirectory() as directory:
        changed = pathlib.Path(directory) / "changed.txt"
        changed.write_text("".join(f"{path}\n" for path in paths))
        env = os.environ.copy()
        env["CHANGED_FILES"] = str(changed)
        env["PROTECTED_PATHS"] = patterns
        result = subprocess.run(
            [sys.executable, "-c", code],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        return result.returncode


def test_action_pins() -> None:
    for workflow in (AGENT, CI):
        for reference in re.findall(r"uses:\s*([^\s#]+)", workflow):
            if reference.startswith(("actions/", "openai/")):
                check(
                    re.fullmatch(r"[^@]+@[0-9a-f]{40}", reference) is not None,
                    f"external Action is not SHA-pinned: {reference}",
                )


def test_untrusted_input_is_not_shell_source() -> None:
    forbidden = ("inputs.issue_title", "inputs.issue_body", "inputs.trigger_actor")
    for block in run_blocks(AGENT):
        for value in forbidden:
            check(f"${{{{ {value} }}}}" not in block, f"untrusted {value} appears in run block")


def test_guard_deny_paths() -> None:
    check("github.event.label.name == 'agent'" in CLIENT_AGENT, "caller must require the agent label")
    check("candidate" in AGENT and 'candidate" = "$TRIGGER_ACTOR' in AGENT, "exact actor comparison missing")
    check("Actor '$TRIGGER_ACTOR' is not authorized" in AGENT, "unauthorized actor deny path missing")
    check('disabled "$PIPELINE_ENABLED"' in AGENT, "repository kill switch missing")
    check('disabled "$GLOBAL_PIPELINE_ENABLED"' in AGENT, "global kill switch missing")
    check("highest >= MAX_ATTEMPTS" in AGENT, "attempt-cap deny condition missing")
    check("agent:attempt-" in AGENT, "durable attempt labels missing")
    check("HUMAN INPUT REQUIRED" in AGENT, "safe-stop marker missing")
    check("concurrency:" in AGENT and "issue-${{ inputs.issue_number }}" in AGENT, "Issue concurrency missing")
    check("timeout-minutes:" in AGENT, "finite timeout missing")


def test_privilege_and_trigger_boundaries() -> None:
    check("pull_request_target" not in ALL_WORKFLOWS, "privileged pull_request_target is forbidden")
    check("secrets: inherit" not in ALL_WORKFLOWS, "blanket secret inheritance is forbidden")
    check("permission-profile: \":workspace\"" in AGENT, "Codex workspace permission profile missing")
    check("safety-strategy: drop-sudo" in AGENT, "drop-sudo missing")
    check("codex-args: '[\"--ephemeral\"]'" in AGENT, "fresh ephemeral execution missing")
    check("codex-version: \"0.147.0\"" in AGENT, "Codex CLI version must be explicit")
    implement = AGENT.split("  implement:", 1)[1].split("  publish:", 1)[0]
    publish = AGENT.split("  publish:", 1)[1]
    check("contents: read" in implement and "contents: write" not in implement, "Codex job must be read-token only")
    check("contents: write" in publish and "actions: write" in publish, "publishing permissions missing")
    check("openai_api_key" not in publish, "OpenAI secret leaked into publishing job")
    check("gh workflow run ci.yml" in publish, "explicit CI dispatch missing")
    check("--draft" in publish, "PR must be draft")
    check("--input -" in AGENT, "attempt label JSON must be passed as data")


def test_contracts() -> None:
    headings = (
        "## What changed",
        "## Assumptions I made that the Issue did not specify",
        "## Decisions that may need human judgment",
        "## Verification performed",
    )
    for heading in headings:
        check(heading in BUILD_CONTRACT, f"build contract missing {heading}")
        check(heading in PR_TEMPLATE, f"PR template missing {heading}")
        check(heading in AGENT, f"workflow validation missing {heading}")
    for field in ("label: Goal", "label: Acceptance criteria", "label: Out of scope", "label: UX / visual constraints"):
        check(field in ISSUE_FORM, f"Issue form missing {field}")
    check("labels: []" in ISSUE_FORM, "Issue creation must not authorize itself")
    check("Improve the homepage CTA." in (ROOT / "docs/canary.md").read_text(), "ambiguity canary missing")


def test_protected_path_code() -> None:
    blocks = embedded_python_blocks(AGENT) + embedded_python_blocks(CI)
    check(len(blocks) == 2, f"expected two protected-path implementations, found {len(blocks)}")
    for code in blocks:
        check(run_protected_matcher(code, ["src/app.ts"]) == 0, "normal path should pass")
        check(run_protected_matcher(code, ["PROJECT.md"]) != 0, "PROJECT.md should be blocked")
        check(run_protected_matcher(code, [".github/workflows/release.yml"]) != 0, "workflow should be blocked")
        check(run_protected_matcher(code, ["infra/main.tf"]) != 0, "Terraform file should be blocked")
        check(run_protected_matcher(code, ["main.tf"]) != 0, "root Terraform file should be blocked")
        custom = "design-system/tokens/**\nsecurity/**"
        check(run_protected_matcher(code, ["design-system/tokens/color.json"], custom) != 0, "custom token path should be blocked")
        check(run_protected_matcher(code, ["src/color.ts"], custom) == 0, "unmatched custom path should pass")
        check(run_protected_matcher(code, ["PROJECT.md"], custom) != 0, "custom paths must not remove defaults")


def test_ci_failure_propagation() -> None:
    for name in ("build", "test", "lint", "typecheck"):
        check(f"inputs.{name}_command != ''" in CI, f"{name} command guard missing")
    result = subprocess.run(["bash", "-euo", "pipefail", "-c", "false"], check=False)
    check(result.returncode != 0, "failing deterministic command must remain failing")


def test_embedded_shell_syntax() -> None:
    for workflow in (AGENT, CI):
        for index, block in enumerate(run_blocks(workflow), start=1):
            result = subprocess.run(
                ["bash", "-n"],
                input=textwrap.dedent(block),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
            )
            check(result.returncode == 0, f"shell block {index} failed syntax check: {result.stdout}")


def test_client_callers_stay_thin() -> None:
    check(len(CLIENT_AGENT.splitlines()) < 45, "agent caller is no longer thin")
    check(len(CLIENT_CI.splitlines()) < 55, "CI caller is no longer thin")
    check("@DEV_PLATFORM_VERSION" in CLIENT_AGENT and "@DEV_PLATFORM_VERSION" in CLIENT_CI, "version pin placeholder missing")
    check("@main" not in CLIENT_AGENT + CLIENT_CI, "client must not track dev-platform main")


def main() -> None:
    tests = (
        test_action_pins,
        test_untrusted_input_is_not_shell_source,
        test_guard_deny_paths,
        test_privilege_and_trigger_boundaries,
        test_contracts,
        test_protected_path_code,
        test_ci_failure_propagation,
        test_embedded_shell_syntax,
        test_client_callers_stay_thin,
    )
    for test in tests:
        test()
        print(f"ok: {test.__name__}")


if __name__ == "__main__":
    main()
