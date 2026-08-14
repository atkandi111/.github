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
CLIENT_SETUP = ROOT / "client-setup"
AGENT = (ROOT / ".github/workflows/agent.yml").read_text()
CI = (ROOT / ".github/workflows/ci.yml").read_text()
CLIENT_AGENT = (ROOT / "templates/client/.github/workflows/agent.yml").read_text()
CLIENT_CI = (ROOT / "templates/client/.github/workflows/ci.yml").read_text()
ISSUE_FORM = (ROOT / "templates/client/.github/ISSUE_TEMPLATE/agent-task.yml").read_text()
README = (ROOT / "README.md").read_text()
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


def run_guard(
    *,
    pipeline_enabled: str = "true",
    global_pipeline_enabled: str = "true",
    trigger_actor: str = "maintainer",
    authorized_actors: str = "maintainer",
    labels: tuple[str, ...] = (),
    max_attempts: str = "3",
) -> tuple[int, dict[str, str], str, str]:
    guard = textwrap.dedent(run_blocks(AGENT)[0])
    with tempfile.TemporaryDirectory() as directory:
        root = pathlib.Path(directory)
        fake_bin = root / "bin"
        fake_bin.mkdir()

        gh_calls = root / "gh-calls.txt"
        fake_gh = fake_bin / "gh"
        fake_gh.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" >> "$FAKE_GH_CALLS"
if [[ "$1" == "api" && "${3:-}" == "--jq" ]]; then
  printf '%s' "$FAKE_LABELS"
fi
cat >/dev/null || true
"""
        )
        fake_gh.chmod(0o755)

        fake_jq = fake_bin / "jq"
        fake_jq.write_text(
            """#!/usr/bin/env bash
set -euo pipefail
printf '{"labels":["%s"]}\\n' "$4"
"""
        )
        fake_jq.chmod(0o755)

        github_output = root / "github-output.txt"
        summary = root / "summary.md"
        runner_temp = root / "runner-temp"
        runner_temp.mkdir()
        env = os.environ.copy()
        env.update(
            {
                "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
                "GITHUB_OUTPUT": str(github_output),
                "GITHUB_STEP_SUMMARY": str(summary),
                "GITHUB_REPOSITORY": "example/client",
                "ISSUE_NUMBER": "17",
                "TRIGGER_ACTOR": trigger_actor,
                "AUTHORIZED_ACTORS": authorized_actors,
                "PIPELINE_ENABLED": pipeline_enabled,
                "GLOBAL_PIPELINE_ENABLED": global_pipeline_enabled,
                "MAX_ATTEMPTS": max_attempts,
                "RUNNER_TEMP": str(runner_temp),
                "FAKE_GH_CALLS": str(gh_calls),
                "FAKE_LABELS": "".join(f"{label}\n" for label in labels),
            }
        )
        result = subprocess.run(
            ["bash", "-euo", "pipefail", "-c", guard],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        outputs: dict[str, str] = {}
        if github_output.exists():
            for line in github_output.read_text().splitlines():
                key, value = line.split("=", 1)
                outputs[key] = value
        summary_text = summary.read_text() if summary.exists() else ""
        calls = gh_calls.read_text() if gh_calls.exists() else ""
        return result.returncode, outputs, summary_text, calls


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


def test_guard_contract() -> None:
    check("github.event.label.name == 'agent'" in CLIENT_AGENT, "caller must require the agent label")
    check("candidate" in AGENT and 'candidate" = "$TRIGGER_ACTOR' in AGENT, "exact actor comparison missing")
    check("Actor '$TRIGGER_ACTOR' is not authorized" in AGENT, "unauthorized actor deny path missing")
    check('enabled "$PIPELINE_ENABLED"' in AGENT, "repository explicit-enable guard missing")
    check('enabled "$GLOBAL_PIPELINE_ENABLED"' in AGENT, "global explicit-enable guard missing")
    check(AGENT.count('default: "false"') >= 2, "kill-switch inputs must default to false")
    check("highest >= MAX_ATTEMPTS" in AGENT, "attempt-cap deny condition missing")
    check("agent:attempt-" in AGENT, "durable attempt labels missing")
    check("HUMAN INPUT REQUIRED" in AGENT, "safe-stop marker missing")
    check("concurrency:" in AGENT and "issue-${{ inputs.issue_number }}" in AGENT, "Issue concurrency missing")
    check("timeout-minutes:" in AGENT, "finite timeout missing")


def test_guard_behavior() -> None:
    code, outputs, _, _ = run_guard()
    check(code == 0, "authorized explicitly enabled guard should pass")
    check(outputs.get("proceed") == "true", "enabled guard should proceed")
    check(outputs.get("attempt") == "1", "first enabled run should reserve attempt 1")

    for value in ("", "false", "TRUE", "yes", "1"):
        code, outputs, summary, calls = run_guard(pipeline_enabled=value)
        check(code == 0, f"repository enable value {value!r} should stop safely")
        check(outputs.get("proceed") == "false", f"repository enable value {value!r} should not proceed")
        check("not explicitly enabled" in summary, "repository disabled summary missing")
        check(calls == "", "disabled repository guard should not call GitHub")

        code, outputs, summary, calls = run_guard(global_pipeline_enabled=value)
        check(code == 0, f"organization enable value {value!r} should stop safely")
        check(outputs.get("proceed") == "false", f"organization enable value {value!r} should not proceed")
        check("not explicitly enabled" in summary, "organization disabled summary missing")
        check(calls == "", "disabled organization guard should not call GitHub")

    code, outputs, _, _ = run_guard(trigger_actor="intruder")
    check(code != 0, "unauthorized actor should fail")
    check(outputs.get("proceed") == "false", "unauthorized actor should not proceed")

    code, outputs, summary, calls = run_guard(labels=("agent:attempt-1", "agent:attempt-3"))
    check(code == 0, "attempt cap should stop safely")
    check(outputs.get("proceed") == "false", "attempt cap should not proceed")
    check("Attempt cap reached" in summary, "attempt-cap summary missing")
    check("issue comment" in calls, "attempt cap should leave a human-input comment")

    code, outputs, _, _ = run_guard(labels=("agent:attempt-1",))
    check(code == 0, "run below the attempt cap should pass")
    check(outputs.get("proceed") == "true", "run below the attempt cap should proceed")
    check(outputs.get("attempt") == "2", "run below the attempt cap should reserve the next attempt")


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
        check(heading in AGENT, f"workflow validation missing {heading}")
        check(heading in README, f"README agent contract missing {heading}")
    for field in ("label: Goal", "label: Acceptance criteria", "label: Out of scope", "label: UX / visual constraints"):
        check(field in ISSUE_FORM, f"Issue form missing {field}")
    check("labels: []" in ISSUE_FORM, "Issue creation must not authorize itself")
    check("Improve the homepage CTA." in README, "ambiguity canary missing")


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
    check("DEV_PLATFORM_VERSION" not in CLIENT_AGENT + CLIENT_CI, "obsolete version placeholder remains")
    check(CLIENT_AGENT.count("@main") == 1, "agent caller must follow dev-platform main")
    check(CLIENT_CI.count("@main") == 1, "CI caller must follow dev-platform main")


def test_client_setup() -> None:
    candidate_sha = "a" * 40
    with tempfile.TemporaryDirectory() as directory:
        target = pathlib.Path(directory) / "client"
        target.mkdir()
        result = subprocess.run(
            [str(CLIENT_SETUP), "install", str(target), "example/dev-platform"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        check(result.returncode == 0, f"client install failed: {result.stdout}")
        for relative in (
            "AGENTS.md",
            "PROJECT.md",
            ".github/ISSUE_TEMPLATE/agent-task.yml",
            ".github/workflows/agent.yml",
            ".github/workflows/ci.yml",
        ):
            check((target / relative).is_file(), f"client install missed {relative}")
        callers = (target / ".github/workflows/agent.yml").read_text() + (target / ".github/workflows/ci.yml").read_text()
        check("example/dev-platform/.github/workflows/agent.yml@main" in callers, "agent main reference missing")
        check("example/dev-platform/.github/workflows/ci.yml@main" in callers, "CI main reference missing")

        collision = subprocess.run(
            [str(CLIENT_SETUP), "install", str(target), "example/dev-platform"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        check(collision.returncode != 0, "client install should refuse collisions")

        incomplete = subprocess.run(
            [str(CLIENT_SETUP), "check", str(target)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        check(incomplete.returncode != 0, "template guidance should fail readiness")

        (target / "PROJECT.md").write_text("# Project\n\nA confirmed product contract.\n")
        (target / "AGENTS.md").write_text("# Agent instructions\n\nRun the repository checks.\n")
        ready = subprocess.run(
            [str(CLIENT_SETUP), "check", str(target)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        check(ready.returncode == 0, f"completed client setup should pass: {ready.stdout}")

        ci_caller = target / ".github/workflows/ci.yml"
        ci_caller.write_text(
            ci_caller.read_text()
            + "\n  preview:\n    runs-on: ubuntu-latest\n    steps:\n"
            + "      - uses: actions/checkout@" + "c" * 40 + "\n"
        )
        extended = subprocess.run(
            [str(CLIENT_SETUP), "check", str(target)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        check(extended.returncode == 0, f"additional client Actions should not confuse reference validation: {extended.stdout}")

        original_ci = ci_caller.read_text()
        ci_caller.write_text(original_ci.replace("@main", "@" + "b" * 40))
        mismatched = subprocess.run(
            [str(CLIENT_SETUP), "check", str(target)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        check(mismatched.returncode != 0, "normal client pinned away from main should fail readiness")
        ci_caller.write_text(original_ci)

        canary = pathlib.Path(directory) / "canary"
        canary.mkdir()
        canary_install = subprocess.run(
            [str(CLIENT_SETUP), "install-canary", str(canary), "example/dev-platform", candidate_sha],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        check(canary_install.returncode == 0, f"canary install failed: {canary_install.stdout}")
        canary_callers = (canary / ".github/workflows/agent.yml").read_text() + (canary / ".github/workflows/ci.yml").read_text()
        check(canary_callers.count("@" + candidate_sha) == 2, "canary callers must pin the same candidate SHA")
        (canary / "PROJECT.md").write_text("# Project\n\nA confirmed canary product contract.\n")
        (canary / "AGENTS.md").write_text("# Agent instructions\n\nRun the canary checks.\n")
        canary_ready = subprocess.run(
            [str(CLIENT_SETUP), "check-canary", str(canary)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        check(canary_ready.returncode == 0, f"candidate-pinned canary should pass: {canary_ready.stdout}")
        normal_check = subprocess.run(
            [str(CLIENT_SETUP), "check", str(canary)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        check(normal_check.returncode != 0, "candidate-pinned canary must not pass normal client readiness")

        invalid_canary = pathlib.Path(directory) / "invalid-canary"
        invalid_canary.mkdir()
        invalid = subprocess.run(
            [str(CLIENT_SETUP), "install-canary", str(invalid_canary), "example/dev-platform", "main"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        check(invalid.returncode != 0, "canary install must reject a mutable main candidate")
        check(not any(invalid_canary.iterdir()), "rejected canary install should not write files")


def main() -> None:
    tests = (
        test_action_pins,
        test_untrusted_input_is_not_shell_source,
        test_guard_contract,
        test_guard_behavior,
        test_privilege_and_trigger_boundaries,
        test_contracts,
        test_protected_path_code,
        test_ci_failure_propagation,
        test_embedded_shell_syntax,
        test_client_callers_stay_thin,
        test_client_setup,
    )
    for test in tests:
        test()
        print(f"ok: {test.__name__}")


if __name__ == "__main__":
    main()
