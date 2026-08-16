# dev-platform

`dev-platform` is a deliberately small implementation pipeline for isolated
client repositories. An authorized GitHub Issue becomes a reviewable Codex
change; infrastructure, production deployment, product decisions, and merging
remain human-owned.

```text
Issue + agent label
→ authorization and safety guards
→ fresh Codex implementation
→ isolated branch and draft PR
→ deterministic client CI
→ optional client-owned preview
→ human review and merge decision
```

There is no planner, AI reviewer, auto-merge, production deployment, Terraform
access, model routing, or orchestration service. Add another subsystem only
after repeated real-world evidence justifies it.

## Connect a client repository

### Prerequisites

- A private client repository with a documented build/test contract.
- A reviewed `dev-platform` moving `v1` tag that points to a canary-tested,
  immutable `v1.x.y` release. `main` remains the integration branch.
- Permission for the client repository to call this private repository's
  reusable workflows under **Actions → General → Access**.
- Repository policy that permits the workflows' declared `GITHUB_TOKEN`
  permissions and allows GitHub Actions to create pull requests.

Install the five client files, including the hidden `.github` files, with:

```bash
./client-setup install ../client-repository YOUR_ORG/dev-platform
```

The installed callers use `@v1`, so every normal client automatically uses the
latest deliberately released V1 workflow on its next run. The command refuses to
overwrite existing files and never configures GitHub or handles secrets. For
an existing client contract, merge [`templates/client`](templates/client)
manually and keep both reusable workflow references on `@v1`. Then validate
local readiness with:

```bash
./client-setup check ../client-repository
```

Moving `v1` affects every normal client on its next run, so it is a deliberate
release action, not an automatic consequence of merging `main`. Every release
must go through a pull request, review, exact-SHA canary testing, and the local
test suite. Direct and force pushes to `main` are prohibited by policy, and all
available kill switches must remain ready. Enable branch protection immediately
when the repository becomes public or its plan supports it. A dedicated
non-client canary is the only repository that may temporarily pin a candidate
SHA.

Complete `PROJECT.md` with confirmed human-owned product direction and
`AGENTS.md` with the repository map, commands, and engineering conventions.
Create the `agent` label, then configure the following GitHub values.

### Configure OpenAI workload identity

An OpenAI organization owner must create a GitHub Actions Workload Identity
Provider under **Organization settings → Security → Workload Identity
Provider**. Use:

- Issuer: `https://token.actions.githubusercontent.com`
- Audience: a stable value such as `https://api.openai.com/v1`
- GitHub OIDC discovery; do not upload private key material.

Map the provider to a dedicated OpenAI project service account with only
`api.model.read` and `api.model.request`. Match the exact client repository,
caller `workflow_ref`, and reusable `job_workflow_ref` claims. For a normal
client, the reusable workflow claim should end in
`dev-platform/.github/workflows/agent.yml@refs/tags/v1`. Use a separate
non-production mapping for the canary; it may use a trailing wildcard after the
same workflow path so exact candidate SHAs can be tested. Do not trust only the
repository owner or a broad organization wildcard.

OpenAI's setup guide explains the dashboard fields and claim formats:
[GitHub Actions workload identity federation](https://developers.openai.com/api/docs/guides/workload-identity-federation/github-actions).

Required variables:

- `OPENAI_WIF_AUDIENCE` — exact audience configured on the provider.
- `OPENAI_IDENTITY_PROVIDER_ID` — ID of that OpenAI provider.
- `OPENAI_SERVICE_ACCOUNT_ID` — ID of the mapped project service account.
- `AGENT_AUTHORIZED_ACTORS` — comma-separated exact GitHub usernames allowed to
  authorize a run. Start with one maintainer.
- `PIPELINE_ENABLED` — must be exactly `true`; missing, invalid, or any other
  value prevents new runs.
- `AGENT_PIPELINE_ENABLED` — must be exactly `true`. Define it once as an
  organization variable when clients are organization-owned. For repositories
  owned by a personal account, define it separately in every repository;
  GitHub provides no account-wide repository variable in that ownership model.
  Missing, invalid, or any other value prevents new runs.

Optional variables:

- `AGENT_PROTECTED_PATHS` — newline-separated path globs added to the immutable
  central defaults.
- `CI_BUILD_COMMAND`, `CI_TEST_COMMAND`, `CI_LINT_COMMAND`, and
  `CI_TYPECHECK_COMMAND` — client-native deterministic commands. Leave a
  genuinely inapplicable command empty.

Existing pre-release clients must deliberately set both enablement variables to
exactly `true`. Earlier workflow versions treated missing values as enabled;
this version stops safely when either value is missing or invalid.

Optional review labels can record why an agent PR needed correction:

```text
agent-friction:intent
agent-friction:scope
agent-friction:design
agent-friction:bug
agent-friction:convention
agent-friction:underspecified
agent-friction:other
```

After 20–30 agent PRs, inspect actual examples and label counts before adding
automation.

## Normal operation

1. A human completes the Agent task Issue form.
2. An authorized actor reviews the request and adds `agent`.
3. The workflow records `agent:attempt-N`, runs Codex, and opens a draft PR from
   `issue/<number>-attempt-<number>`.
4. CI is explicitly dispatched for that branch.
5. A human uses CI, any client-owned preview, and the structured PR body to
   merge, request changes, or reject the proposal.

Remove and re-add `agent` to authorize another attempt. Each label event
consumes one of the three default attempts. Runs are serialized per Issue and
have finite timeouts.

Codex returns `HUMAN INPUT REQUIRED` without creating a branch when meaningful
product or user-visible intent is missing.

### Agent implementation contract

The prompt in `.github/workflows/agent.yml` is canonical. In summary, the Issue
and trusted repository context define scope. Codex must read `PROJECT.md` and
applicable `AGENTS.md` files, avoid protected paths, make only routine
implementation choices, add appropriate tests, and run documented checks. It
must not commit, push, create a PR, change infrastructure, invent product intent,
or introduce a meaningful dependency, service, architecture change, UX flow,
visual direction, or product behavior without authorization.

When a meaningful decision is missing, Codex returns:

```text
HUMAN INPUT REQUIRED

Missing decision:
<one concise question>
```

Otherwise its final report uses exactly these headings:

```markdown
## What changed
## Assumptions I made that the Issue did not specify
## Decisions that may need human judgment
## Verification performed
```

## Stop the pipeline

- One repository: set `PIPELINE_ENABLED=false`.
- Organization-owned portfolio: set the organization variable
  `AGENT_PIPELINE_ENABLED=false`.
- Personal-account repositories: set `AGENT_PIPELINE_ENABLED=false` in every
  connected repository. This is not an atomic portfolio-wide stop.
- Emergency fallback: disable **Agent implementation** in the affected
  repository's Actions UI.

Cancel existing runs from GitHub Actions. Disable the affected OpenAI workload
identity mapping if its trusted claims or service account are suspected to be
wrong. Exchanged tokens expire within one hour and have no refresh token.
Provider budgets and usage alerts remain required operational controls.

## Security and architecture

Client repositories own product truth in `PROJECT.md`, engineering context in
`AGENTS.md`, application code, and two thin workflow callers. `dev-platform`
owns the reusable workflows and safety conventions. Shared infrastructure,
Terraform, IAM, DNS, runtime resources, and production delivery stay outside
the agent and CI paths.

Trust boundaries:

- The `agent` label authorizes API use and a proposed change only when the event
  actor exactly matches the configured allowlist.
- Issue title/body and GitHub metadata are untrusted data. They are delimited in
  the prompt and never interpolated into shell source.
- The implementation job alone receives `id-token: write`. It exchanges the
  GitHub OIDC identity for a short-lived OpenAI access token, then clears the
  OIDC request environment before starting Codex.
- Codex receives repository read permission, the `:workspace` permission
  profile, `drop-sudo`, an ephemeral session, and access through the Action's
  protected API proxy. It receives neither a long-lived OpenAI key nor the
  write token used for publication.
- The Codex job captures only a binary patch and final message. No repository
  script executes after Codex in that job.
- A clean publishing job without OpenAI credentials validates the patch and
  protected paths before receiving the narrow permissions needed to push a
  branch, create a draft PR, label it, and dispatch CI.
- Agent-written code never runs with privileged secrets. `pull_request_target`
  is forbidden.
- Preview remains client-owned because providers and credentials vary. Preview
  credentials must be non-production and narrowly scoped.

The reusable CI workflow accepts optional `build`, `test`, `lint`, and
`typecheck` command strings. The platform supplies no framework configuration;
empty commands are reported as skipped.

### Preview contract

A client may add a separate `preview` job after `verify` in its CI caller. It
must deploy the exact PR head SHA, publish the preview URL on the PR, use a
limited non-production GitHub Environment, and fail independently without
weakening deterministic CI. Never pass preview secrets through the reusable CI
workflow.

### Design decisions

Publication and reasoning are separate jobs so Codex never shares a write token
with OpenAI access. Fixed patch capture and artifact upload are the only
post-Codex operations in the reasoning job.

V1 uses native OpenAI workload identity federation instead of a stored API key.
The trusted workflow exchanges GitHub's signed OIDC token for an OpenAI bearer
token that lasts at most one hour. The existing Codex Action proxy then isolates
that bearer token from the Codex process. OpenAI provider and service-account
IDs are identifiers stored as GitHub variables, not credentials.

The publisher explicitly dispatches `ci.yml` because most events created by a
repository `GITHUB_TOKEN` do not recursively start workflows. This requires
narrow `actions: write` permission but avoids a PAT or GitHub App. CI also
listens for ordinary pull requests created by humans.

V1 rejects a GitHub App installation token because it adds an application and
key lifecycle without demonstrated need. It also rejects relying on recursive
PR/push events and running all CI inside the agent workflow because those
options are respectively unreliable and couple independently rerunnable
lifecycles.

References: [GitHub workflow triggering](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow),
[reusable workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows),
the [OpenAI Codex GitHub Action](https://learn.chatgpt.com/docs/github-action),
and [OpenAI workload identity token exchange](https://developers.openai.com/api/reference/workload-identity-federation).

## Test and merge a platform change

Never test an unproven platform change by merging it to `main`. Work on a
branch, commit and push the candidate, run `./tests/run.sh`, and review the
complete diff. Then install or temporarily update a dedicated private canary
repository with no production credentials to the exact candidate commit:

```bash
candidate_sha=$(git rev-parse HEAD)
./client-setup install-canary ../dev-platform-canary YOUR_ORG/dev-platform "$candidate_sha"
./client-setup check-canary ../dev-platform-canary
```

For an existing canary, temporarily replace both `@v1` workflow references
with the same full candidate SHA and run `check-canary`. Normal client
repositories must remain on `@v1`.

Required canary cases:

| Case | Issue/change | Expected evidence |
| --- | --- | --- |
| Trivial | Change known copy with exact desired text. | Draft PR contains only the change; CI passes. |
| Normal UI | Specify a bounded UI change and visual constraints. | Normal implementation, structured PR body, CI pass. |
| Feature | Specify a straightforward feature and acceptance tests. | Implementation and tests stay in scope; CI passes. |
| CI failure | Intentionally fail one configured check. | Deterministic CI is red. |
| Protected path | Request a change to `PROJECT.md` or `.github/workflows/**`. | No agent branch is published; the protected-path gate fails. CI also rejects an equivalent human PR. |
| Underspecified | `Improve the homepage CTA.` | The Issue receives `HUMAN INPUT REQUIRED`; no branch or PR is created. |
| Identity mismatch | Use a claim that does not match the OpenAI workload mapping. | Token exchange fails; Codex and publication do not run. |

Also verify both sides of every guard: authorized and unauthorized actor, each
kill switch set to `true` and disabled/unset, complete and incomplete workload
identity configuration, matching and mismatched identity claims, first through
third attempts and a fourth attempt, normal and protected paths, same-Issue
concurrency, and finite timeouts. Restore variables after each case.

Record run links, PRs/comments, labels, checks, and preview URLs. After all
cases pass:

1. Attach the canary evidence to the `dev-platform` pull request.
2. Confirm the organization kill switch, or every required personal-account
   repository switch, can stop new runs.
3. Merge the reviewed candidate into `main` through its pull request. Enforce
   this with branch protection when the repository plan or visibility permits.
4. Pin the canary to the exact merged `main` SHA and confirm the required suite
   is still green. This matters when the merge strategy creates a new commit.
5. Create the next immutable release tag, such as `v1.0.0`, at that exact tested
   SHA. Then deliberately move the compatibility tag `v1` to the same SHA.
6. Normal clients automatically consume the new `v1` workflow on their next
   run; monitor the first executions closely.

For an incident, set `AGENT_PIPELINE_ENABLED=false` before doing anything else:
once at organization scope, or in every personal-account client repository.
Point `v1` back to the previous known-good immutable `v1.x.y` release, verify
that exact SHA in the canary, and then re-enable the pipeline. Separately revert
the offending `main` change through the same reviewed workflow. Do not
force-push or rewrite `main`.

Current external pins, verified 2026-08-13:

| Component | Version | Immutable SHA |
| --- | --- | --- |
| `openai/codex-action` | `v1.11` | `52fe01ec70a42f454c9d2ebd47598f9fd6893d56` |
| Codex CLI | `0.147.0` | Fixed through the Action input |
| `actions/checkout` | `v4.3.1` | `34e114876b0b11c390a56381ad16ebd13914f8d5` |
| `actions/upload-artifact` | `v7.0.1` | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` |
| `actions/download-artifact` | `v8.0.1` | `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` |

Reverify the official manifest, release tag, and full SHA deliberately when
updating a pin.
