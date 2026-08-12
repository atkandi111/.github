# Operations

## Client setup

Use a private `dev-platform` repository by default. In its **Actions → General → Access** settings, allow the intended private client repositories to call reusable workflows. Copy `templates/client` into the canary/client and replace every `YOUR_ORG/dev-platform` plus `DEV_PLATFORM_VERSION` placeholder with a canary-tested tag or full commit SHA.

Create the `agent` label. Also create these optional PR correction labels for lightweight friction tracking:

```text
agent-friction:intent
agent-friction:scope
agent-friction:design
agent-friction:bug
agent-friction:convention
agent-friction:underspecified
agent-friction:other
```

Apply one or more correction labels during human review. After 20–30 agent PRs, inspect label counts and review examples before adding automation.

### Required secret

- `OPENAI_API_KEY`: OpenAI API credential used only by the Codex job through the official Action. Never expose it to preview or application code.

### Required variables

- `AGENT_AUTHORIZED_ACTORS`: comma-separated exact GitHub usernames allowed to authorize runs. Start with one maintainer.
- `PIPELINE_ENABLED`: set to `true`; `false` prevents new repository runs.
- Organization variable `AGENT_PIPELINE_ENABLED`: set to `true`; `false` is the portfolio kill switch when organization variables are available.

### Optional variables

- `AGENT_PROTECTED_PATHS`: newline-separated path globs added to the central defaults. Clients cannot remove the workflow, agent-instruction, infrastructure, or Terraform defaults.
- `CI_BUILD_COMMAND`, `CI_TEST_COMMAND`, `CI_LINT_COMMAND`, `CI_TYPECHECK_COMMAND`: client-native deterministic commands. Leave a genuinely inapplicable command empty.
- `CI_TIMEOUT_MINUTES`: currently documented for future tuning; V1 intentionally uses a central finite timeout.

Repository/organization policy must allow the workflow's declared `GITHUB_TOKEN` permissions and allow GitHub Actions to create pull requests. Do not add a PAT or GitHub App unless canary evidence shows the explicit CI dispatch design is insufficient.

## Normal operation

1. A human completes the Issue template.
2. An authorized actor adds `agent`.
3. The workflow records `agent:attempt-N` (maximum three), runs Codex, and opens a draft PR.
4. CI is explicitly dispatched for the branch. Human reviewers use CI, a client-owned preview if present, and the structured PR body.
5. A human merges, requests changes, or rejects. For another attempt, remove then re-add `agent`; each event consumes an attempt.

The workflow serializes runs per Issue and gives the Codex job a finite timeout. Configure OpenAI project budgets/usage alerts separately.

## Kill switches and incidents

Set the repository variable `PIPELINE_ENABLED=false` for one client or organization variable `AGENT_PIPELINE_ENABLED=false` for the portfolio, then cancel active runs. As an emergency fallback, disable **Agent implementation** in each affected repository from the Actions UI. Rotate `OPENAI_API_KEY` if exposure is suspected.

Production credentials, Terraform, IAM, DNS, and shared cloud resources must never be added to this path. Preview credentials, when a client has them, belong in a separate environment with limited scope and no production access.

## Preview contract

There is no universal preview command. A client may add a separate `preview` job after `verify` in its CI caller. The job must deploy exactly the PR head SHA, publish the preview URL on the PR, use a GitHub Environment with limited non-production credentials, and fail independently without weakening deterministic CI. Never pass preview secrets through the reusable CI workflow.

## Version and rollout

Pins verified on 2026-08-13:

| Component | Version/tag | Immutable workflow SHA |
| --- | --- | --- |
| `openai/codex-action` | `v1.11` | `52fe01ec70a42f454c9d2ebd47598f9fd6893d56` |
| Codex CLI | `0.147.0` | npm version fixed through the Action input |
| `actions/checkout` | `v4.3.1` | `34e114876b0b11c390a56381ad16ebd13914f8d5` |
| `actions/upload-artifact` | `v7.0.1` | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` |
| `actions/download-artifact` | `v8.0.1` | `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` |

Re-verify the official manifest, release tag, and full SHA deliberately when updating a pin.

1. Make and locally test a platform change.
2. Point the canary caller at the exact candidate commit and run all canary cases.
3. Create a simple annotated tag such as `v0.1.0` only after canary success.
4. Update one or two clients to that tag; observe before broader rollout.
5. Never point client callers at `main`.

To stop consuming a bad version, restore the prior tested tag in the tiny client callers. Do not force-move release tags.
