# Security and authentication

This pipeline assumes private, mostly solo-maintained repositories. Its guards
primarily prevent automation mistakes, stale results, credential mixing, and
accidental scope expansion; they are not an enterprise approval system.

## Authentication now and later

Use one non-production OpenAI automation project, with a different restricted
service account and key for each connected repository. Separate keys let one
client be revoked independently and make usage attributable without requiring a
separate billing account per client.

The current restricted-key minimum is:

- **List models: Read**
- **Model capabilities: Request**

Leave unrelated resources disabled. Store the key only as that repository's
`OPENAI_API_KEY` Actions secret:

```bash
gh secret set OPENAI_API_KEY --repo OWNER/REPOSITORY
```

Paste it at the hidden prompt. Do not put it in a command argument, file,
repository variable, application environment, or shared organization secret.
A ChatGPT subscription does not fund API calls; configure API billing, a small
project budget, and usage alerts before the first canary.

### Future OIDC migration

OIDC remains the intended keyless upgrade. As of 2026-08-17, GitHub-to-OpenAI
token exchange works, but the official `openai/codex-action@v1.11` proxy accepts
credentials through a fixed 1,024-byte input and cannot accept the longer
workload token. Do not bypass that boundary with a custom proxy or by exposing
the token directly to Codex.

When an immutable official Codex Action release supports the workload token:

1. Prove that exact Action SHA in the canary.
2. Reuse the OpenAI workload identity provider and add an exact mapping for each
   repository's service account, repository, trusted ref, and
   `job_workflow_ref`.
3. Give the thin caller `id-token: write`, replace the API-key secret mapping
   with the non-secret provider values, and perform the exchange centrally.
4. Run the complete canary again, then delete that repository's API key.

Only the authentication edge changes. Issue handling, implementation,
publishing, CI, and review remain the same.

References: [OpenAI workload identity federation](https://developers.openai.com/api/docs/guides/workload-identity-federation/github-actions)
and the upstream [Codex proxy credential input](https://github.com/openai/codex/blob/main/codex-rs/responses-api-proxy/src/read_api_key.rs).

## Trust and privilege boundaries

- The `agent` label authorizes API use and a proposed change only when the event
  actor exactly matches `AGENT_AUTHORIZED_ACTORS` and both kill switches are
  exactly `true`.
- Issue title, body, and GitHub metadata are passed as delimited action data,
  never interpolated into executable shell.
- Codex receives `contents: read`, the `:workspace` permission profile,
  `drop-sudo`, and an ephemeral session. The official Action proxy holds the
  OpenAI key. Codex never receives the publishing token.
- The Codex job exports only a binary patch and final report. It executes no
  repository script after Codex finishes.
- The separate publishing job has narrow GitHub write permissions for its whole
  job, but validates the patch and protected paths before using them to push,
  create a draft PR, label it, or dispatch CI. It has no OpenAI credential.
- Deterministic client commands run with `contents: read` only. Separate pending
  and final status jobs use clean runners with `statuses: write`; they never
  check out code, consume artifacts or client outputs, or execute client commands.
- Agent-written code never runs with privileged secrets. `pull_request_target`
  and blanket secret inheritance are forbidden.
- Production credentials, shared infrastructure, IAM, DNS, and deployment stay
  outside both the implementation and deterministic CI paths.

## Protected paths

The immutable defaults protect:

```text
PROJECT.md
AGENTS.md and nested AGENTS.md files
.github/workflows and everything below it
.github/actions and everything below it
infrastructure and everything below it
terraform and everything below it
all .tf and .tfvars files
```

`AGENT_PROTECTED_PATHS` may add newline-separated globs but cannot remove these
defaults. Both publishing and CI consume NUL-delimited Git output, so legal
filenames containing newlines remain one path. Exact protected directory roots
are blocked as well as their descendants.

## Exact-commit CI

The publisher dispatches the unchanged client `ci.yml` caller on the newly
published agent branch, so the run records the PR branch and head. The protected
path gate guarantees the agent patch did not modify that caller. The publisher
also passes the full commit SHA as data; reusable CI rejects mutable refs,
checks out that SHA, verifies `HEAD`, compares it with the requested base, and
only then runs client commands. Because GitHub does not include a
`workflow_dispatch` run in the PR check rollup, isolated clean-runner jobs post
the fixed `dev-platform/deterministic-ci` commit status on that same SHA. The
final writer reads only GitHub's trusted verification-job result, so client code
cannot forge the status through `GITHUB_ENV`, `GITHUB_PATH`, `BASH_ENV`, a fake
`gh`, artifacts, or job outputs.

Ordinary human PRs run through `pull_request`. Opening, synchronizing,
reopening, or editing a PR triggers verification, so changing its base cannot
reuse a stale protected-path comparison.

## Agent report contract

Successful Codex output must contain:

```markdown
## What changed
## Assumptions I made that the Issue did not specify
## Decisions that may need human judgment
## Verification performed
```

The report is advisory. The diff and deterministic CI are authoritative.

## Preview contract

A client may add a separate preview job after deterministic verification. It
must deploy the exact PR head SHA, publish its URL on the PR, use limited
non-production credentials, and fail independently without weakening CI. Never
pass preview secrets through the reusable CI workflow.
