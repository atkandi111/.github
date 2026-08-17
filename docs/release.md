# Canary and release

`main` is the client release channel. Never merge an unproven workflow change
into it. A dedicated private canary must have no production credentials.

## Test a candidate

Run the local suite and capture the exact candidate:

```bash
./tests/run.sh
git diff --check
git rev-parse HEAD
```

Install a new canary at that immutable SHA:

```bash
./client-setup install-canary ../dev-platform-canary YOUR_ORG/dev-platform COMMIT_SHA
./client-setup check-canary ../dev-platform-canary
```

For an existing canary, update both reusable workflow references to the same
full candidate SHA. Normal clients remain on `@main`.

## Required V1 cases

| Case | Request or fixture | Expected evidence |
| --- | --- | --- |
| Trivial | Change known copy to exact supplied text. | Draft PR contains only that change; its PR-head CI passes. |
| Normal UI | Bounded UI change with visual constraints. | Scoped implementation, structured report, and PR-head CI pass. |
| Feature | Straightforward feature with acceptance tests. | Implementation and tests remain in scope; PR-head CI passes. |
| CI failure | Intentionally fail one configured command. | Deterministic CI is red. |
| Protected path | Request `PROJECT.md`, a protected root, or `.github/workflows/**`. | Agent safe-stops or publisher rejects; equivalent human PR fails CI. |
| Underspecified | `Improve the homepage CTA.` | One `HUMAN INPUT REQUIRED` question; no branch or PR. |

Also prove both sides of every guard: authorized and unauthorized actor, each
kill switch enabled and disabled or unset, attempts one through three and the
fourth-attempt cap, normal and protected paths, same-Issue concurrency, mutable
revision rejection, PR-base edits, and finite timeouts. Local behavioral tests
may supply evidence for guards that do not require GitHub itself.

Record run links, PRs or comments, exact SHAs, labels, checks, and any preview
URLs. Canary PRs are evidence and do not need merging.

## Release to clients

1. Attach the exact-candidate evidence to the platform pull request.
2. Obtain an independent review and run the local suite on the final candidate.
3. Confirm the organization kill switch—or every personal-account repository
   switch—can stop new agent runs.
4. Merge the reviewed pull request into `main`. This publishes the workflow for
   normal clients on their next run.
5. Pin the canary to the resulting `main` SHA, run a final smoke check, and
   monitor the first client executions closely.

Enable branch protection for `main` as soon as repository visibility or the
GitHub plan supports it. Until then, use pull requests, review, canary evidence,
and kill switches as compensating controls.

## Roll back

1. Set `AGENT_PIPELINE_ENABLED=false` at organization scope, or disable every
   personal-account client repository.
2. Prepare a reviewed revert of the bad platform change.
3. Canary-test the revert's exact SHA.
4. Merge the revert into `main`, verify the resulting SHA, then re-enable the
   pipeline.

Do not force-push or rewrite `main`.

## Current pins

Verified 2026-08-13:

| Component | Version | Immutable SHA |
| --- | --- | --- |
| `openai/codex-action` | `v1.11` | `52fe01ec70a42f454c9d2ebd47598f9fd6893d56` |
| Codex CLI | `0.147.0` | Fixed through the Action input |
| `actions/checkout` | `v4.3.1` | `34e114876b0b11c390a56381ad16ebd13914f8d5` |
| `actions/upload-artifact` | `v7.0.1` | `043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` |
| `actions/download-artifact` | `v8.0.1` | `3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c` |

Reverify the official release manifest and full SHA deliberately before
updating a pin.
