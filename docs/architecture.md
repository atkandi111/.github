# Architecture

## Implemented V1

```text
GitHub Issue labeled agent by a trusted actor
  → central reusable agent workflow
  → deterministic guards
  → fresh Codex run with a read-only repository token
  → patch artifact
  → separate publishing job
  → isolated branch + draft PR
  → explicit CI workflow dispatch
  → reusable deterministic CI
  → optional client-owned preview
  → human review and merge decision
```

Client repositories retain product truth in `PROJECT.md`, engineering context in `AGENTS.md`, application code, and tiny workflow callers. `dev-platform` owns the reusable workflow implementation and safety conventions. Shared Terraform, IAM, DNS, networking, runtime infrastructure, and production deployment remain outside both the agent and CI paths.

### Trust and privilege boundaries

- The `agent` label is authorization to spend API resources and create a proposed change, but only when the event actor is in the configured allowlist.
- Issue title/body and other GitHub metadata are untrusted. They are passed as data and delimited in the Codex prompt; shell steps consume only quoted environment variables or fixed files.
- Codex gets `contents: read`, a workspace-write sandbox with network disabled by default, and the official Action's default `drop-sudo` safety strategy. It does not get the write token used for publication.
- The publishing job downloads a fixed-name patch artifact into a clean checkout, validates it, rejects protected paths, then receives only the GitHub permissions needed to push, open a draft PR, label it, and dispatch CI.
- Agent-written code never runs with privileged secrets. `pull_request_target` is forbidden.
- Preview is deliberately client-owned because providers and credentials differ. Preview credentials must be non-production and narrowly scoped.

The one unavoidable post-Codex operation in the reasoning job is fixed patch capture and artifact upload. No repository script is executed after Codex. This small exception enables material credential separation without a custom orchestration service.

## Command contract

The reusable CI workflow accepts optional `build`, `test`, `lint`, and `typecheck` command strings. Each client defines its own commands; this platform supplies no shared framework configuration. Empty commands are explicitly reported as skipped.

## Future conceptual loop (not implemented)

```text
Plan → Approve → Build → Verify → Try → Repeat
```

Planning assistance, Issue generation, AI review, model routing, multiple agents, judges, risk scoring, auto-merge, production automation, and Terraform are intentionally absent. A future subsystem is justified only by a recurring observed failure in real agent PRs.

