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
- Active OpenAI API billing with a small project budget and usage alerts. A
  ChatGPT subscription does not fund API calls.

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

Required secret:

- `OPENAI_API_KEY` — a dedicated, non-production OpenAI project
  service-account key used only by the official Codex Action proxy.

### Authentication now and later

Use one OpenAI automation project and create a different service account and
key for each connected repository: canary, Rotary, D'emand, and so on. This is
one OpenAI project, not one project per repository. Separate keys make one
client independently revocable and keep usage attributable. The project shares
the organization's one API billing account, so adding repositories does not
require adding another payment method.

Give each service account only the permissions Codex needs. The current
restricted-key minimum is **List models: Read** and **Model capabilities:
Request**; leave unrelated resources disabled. Store the key once as that
repository's `OPENAI_API_KEY` Actions secret:

```bash
gh secret set OPENAI_API_KEY --repo OWNER/REPOSITORY
```

Paste the key only at the hidden prompt. Do not put it in a command argument,
file, repository variable, or organization-wide shared secret. Personal-account
repositories cannot share an organization Actions secret, but separate keys
are the safer design regardless.

Before the first canary, confirm **OpenAI Platform → Organization → Billing**
has a payment method or credits. Keep the project budget deliberately small;
`Quota exceeded` means authentication reached OpenAI but the API billing balance
or limit does not permit the model request.

OIDC remains the intended keyless upgrade. It is deferred only by a compatibility
gate: as of 2026-08-17, GitHub-to-OpenAI token exchange works in the canary, but
the official `openai/codex-action@v1.11` proxy reads credentials through a fixed
1,024-byte input and cannot accept the longer workload token. Do not add a
custom credential proxy or expose the token directly to Codex to bypass this.

When an official immutable Codex Action SHA supports the workload token:

1. Prove that exact SHA in the canary.
2. Reuse the OpenAI workload identity provider, and add an exact mapping for
   each repository's service account, repository, `main` ref, and trusted
   `job_workflow_ref` at the released `v1` tag.
3. Give the thin caller `id-token: write`, replace its one secret mapping with
   the three non-secret provider, service-account, and audience values, and let
   the central workflow perform the exchange.
4. Run the complete canary again, then delete that repository's API key.

Application code, CI commands, Issue handling, publishing, and review do not
change. Only the authentication edge between the caller and the central Codex
job changes. See the official [OpenAI workload identity federation guide](https://developers.openai.com/api/docs/guides/workload-identity-federation/github-actions)
and the upstream [Codex proxy input implementation](https://github.com/openai/codex/blob/main/codex-rs/responses-api-proxy/src/read_api_key.rs).

Required variables:

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

Cancel existing runs from GitHub Actions. Rotate `OPENAI_API_KEY` if exposure is
suspected. Provider budgets and usage alerts are required operational controls,
not custom services in this repository.

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
- Codex receives repository read permission, the `:workspace` permission
  profile, `drop-sudo`, and an ephemeral session. The official Action proxy
  holds the OpenAI credential; the job does not receive the write token used
  for publication.
- The Codex job captures only a binary patch and final message. No repository
  script executes after Codex in that job.
- A clean publishing job without the OpenAI secret validates the patch and
  protected paths before receiving the narrow permissions needed to push a
  branch, create a draft PR, label it, and dispatch CI.
- Protected-path checks consume NUL-delimited Git output so every legal
  filename, including names containing newlines, is matched as one path.
- The publisher dispatches the trusted base-branch CI caller with the exact
  published commit SHA. CI rejects mutable refs and verifies that checkout
  resolved to that same commit before running client code.
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
with the OpenAI credential. Fixed patch capture and artifact upload are the only
post-Codex operations in the reasoning job.

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
and the [OpenAI Codex GitHub Action](https://learn.chatgpt.com/docs/github-action).

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

Also verify both sides of every guard: authorized and unauthorized actor, each
kill switch set to `true` and disabled/unset, first through third attempts and a
fourth attempt, normal and protected paths, same-Issue concurrency, and finite
timeouts. Restore variables after each case.

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
