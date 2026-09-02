# Atkandi developer platform

This public account-level `.github` repository is the reviewed source for the portfolio's Issue-to-PR pipeline, shared Codex policy, deterministic CI, Project synchronization, and default Issue/PR templates.

## Human summary

The solo-developer workflow has two deliberate human attention points:

1. Write and review an **Implementation Issue** when the work is ready. Publishing that owner-authored Issue queues it automatically.
2. Review the resulting pull request. Approve the current revision to authorize merge, or request changes to send the same PR through one more implementation pass.

Everything between those points is mechanical: one repository-scoped run, one `issue/<number>` branch, one draft PR, a completed Merge Brief, deterministic CI, and native Codex P0/P1 review. Planning / deferred Issues never run. The Project only mirrors status.

Do not add `@codex implement` to an Issue. That invokes a separate native Cloud task and can duplicate the Actions-hosted implementation.

## Architecture at a glance

| Part | Responsibility |
| --- | --- |
| Implementation Issue | Reviewed, repository-scoped work contract. The owner's initial `implementation` label authorizes one queued run. |
| Planning / deferred Issue | Backlog, unresolved planning, or coordination parent; never executable. |
| Per-repository Actions queue | Runs one implementation at a time per repository and retains up to 100 waiting runs with `queue: max`; different repositories run independently. |
| Codex implementation job | Edits an isolated checkout with no GitHub write, publisher, deployment, or production credential. |
| Clean publisher | Validates a provenance-bound patch in a fresh checkout, then uses a short-lived repository-scoped GitHub App token to push and open/update one PR. |
| Deterministic CI | Verifies the exact published SHA without deployment credentials and rejects protected paths. |
| Native Codex Code Review | Starts when the initial draft becomes ready and reports advisory P0/P1 findings. |
| Owner approval | The only merge authorization. A head-bound status prevents an approval for an older revision from satisfying the gate. |
| Native auto-merge | Used only when GitHub can enforce approval, current green checks, stale-review dismissal, and resolved conversations; otherwise merge remains manual. |
| Portfolio Project | Mirrors Todo, In Progress, For Review, and Done for visibility only. |
| Trusted post-merge workflows | Own deployment and persistent/shared infrastructure effects with separate credentials and approval. |

## Normal flow

1. The repository owner creates an Issue through the inherited **Implementation issue** form. The original `opened` event must contain `implementation` and must not contain `planning`.
2. The intake workflow records `agent:authorized` and `agent:in-progress`. Later text, comments, label changes, and Project fields cannot authorize a run.
3. GitHub serializes work per repository. The implementation job reads the Issue as untrusted data and produces a patch artifact plus provenance.
4. A separate clean job revalidates the Issue, receipt, exact start SHA, patch hash, and protected paths. Only then does it mint a one-hour GitHub App installation token scoped to that repository.
5. The publisher creates or updates `issue/<number>` and exactly one draft PR, verifies GitHub's head SHA, and completes the Merge Brief.
6. Credential-free deterministic CI runs on that SHA. A failure leaves the work In Progress on the same PR.
7. Green CI removes the in-progress marker and makes the initial PR ready, which starts automatic native Codex review when enabled in Codex settings.
8. The owner reviews the Merge Brief, diff, CI, and Codex findings. A changes-requested review queues a bounded revision on the same branch and PR. A fresh Codex review on revisions is optional because AI review is advisory.
9. Owner approval creates the head-bound `atkandi/owner-approval` status. Native auto-merge may complete only where repository protections enforce the full gate; private repositories without that GitHub capability retain manual merge.

## Centralized pieces

- `policy/AGENTS.md`: portfolio-wide implementation and review rules.
- `.github/workflows/agent.yml`: reusable authorization, implementation, publication, and handoff pipeline.
- `.github/workflows/owner-approval.yml`: reusable head-bound owner-review status.
- `.github/workflows/ci.yml`: reusable credential-free CI and protected-path gate.
- `.github/workflows/portfolio-project.yml`: scheduled membership and lifecycle reconciliation.
- `.github/ISSUE_TEMPLATE/` and `.github/pull_request_template.md`: account defaults for repositories without local overrides.
- `templates/client/`: thin callers and repository guidance skeletons.
- `client-setup`: conservative installer, release-pin checker, and label setup command.

Client callers follow `atkandi111/.github@main`, so reviewed central workflow updates propagate without copying their implementation. The thin local callers remain necessary because GitHub does not inherit Actions workflows from the account `.github` repository.

## Trust boundaries

- The kill switch is `AGENT_PIPELINE_ENABLED`; it defaults to false. Manual recovery is owner-only and requires the trusted authorization receipt from an earlier valid `opened` event.
- `OPENAI_API_KEY` belongs to a dedicated non-production OpenAI project for that repository. The official Codex Action keeps it behind its proxy; the Codex job receives no GitHub write credential.
- `PUBLISHER_APP_PRIVATE_KEY` is used only by clean publisher/finalizer jobs. Tokens are short-lived and downscoped to one repository and the exact contents/issues/pull-request permissions required.
- Workflow/action paths and all `AGENTS.md` files are publisher-protected. Application callers should additionally protect infrastructure paths; the infrastructure repository may allow credential-free IaC edits and validation.
- Pull-request jobs receive no deployment or persistent infrastructure secrets. Production/shared effects remain post-merge and separately approved.
- Native Codex review may inform the owner but cannot merge, deploy, or change Project authority.

## Adoption

Install the thin callers in a new registered repository:

```bash
./client-setup onboard /path/to/repository atkandi111/.github OWNER/REPOSITORY
./client-setup check /path/to/repository
```

Then create the four required labels, configure the dedicated OpenAI key and publisher App, leave both pipeline variables disabled, merge the reviewed caller PR, verify repository protections, and enable the pipeline. Follow [Cloud and publisher setup](docs/cloud-setup.md) and [Release and rollback](docs/release.md).

For Issue sizing and cross-repository parents, read [Issue planning](docs/issue-planning.md). For the Project lifecycle, read [Governance rollout](docs/governance-rollout.md). For credentials and protected paths, read [Security](docs/security.md).
