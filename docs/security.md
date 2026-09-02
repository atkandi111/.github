# Security and trust boundaries

## Authorization

A new run is authorized only by the immutable combination captured in the original GitHub `issues.opened` event:

- the repository owner authored and opened the Issue;
- the initial label snapshot contains `implementation`; and
- it does not contain `planning`.

The intake workflow records `agent:authorized` as a machine-issued receipt before implementation. Manual recovery and owner-requested revisions require that receipt. A human-added later label, Issue/PR text, comment, Project field, similar wording, or another actor never authorizes execution. Closing the Issue before publication stops the publisher. The repository variable `AGENT_PIPELINE_ENABLED` is the kill switch and defaults to false.

## Queue and attempts

GitHub Actions `queue: max` serializes the reusable workflow by repository: one active run and up to 100 waiting runs. Different repositories have different concurrency groups. Cancellation is disabled and waiting-time FIFO is accepted; the system does not infer dependencies from Issue numbers or prose.

`AGENT_MAX_ATTEMPTS` bounds reruns of the same GitHub event and defaults to two. A manual recovery dispatch is owner-only and requires the earlier trusted receipt. Exceeding GitHub's queue capacity produces a canceled, unexecuted run that must be explicitly recovered.

## Credential separation

| Boundary | Credentials and authority |
| --- | --- |
| Intake | Repository `GITHUB_TOKEN` with Issue/PR metadata and label access; no publisher or production credential. |
| Codex implementation | `contents: read`, Issue read, and one dedicated non-production OpenAI project key through the official Codex Action proxy. No GitHub write, publisher, Project, deployment, or infrastructure credential. |
| Clean publisher/finalizer | A one-hour GitHub App installation token downscoped to the current repository with Administration read and Contents/Issues/Pull requests write. No OpenAI, Project, deployment, or cloud credential. |
| Pull-request CI | `contents: read`; no secret, OIDC, deployment, or persistent-infrastructure authority. |
| Owner approval mirror | Repository status write only; accepts the repository owner's submitted GitHub review for the exact current commit. |
| Portfolio reconciliation | The central `PORTFOLIO_PROJECT_TOKEN`; may add Project items and update Status only. It never reaches implementation or publisher jobs. |

The publisher App private key is required. The workflow fails closed rather than falling back to `GITHUB_TOKEN`, because a workflow-created PR using that token can leave downstream CI waiting for manual workflow approval. The App must be installed only on selected repositories and must not receive Actions, Workflows, Deployments, Environments, Secrets, or cloud permissions.

## Artifact and publisher boundary

Codex edits an isolated checkout and emits only an implementation result, a binary-capable Git patch, and provenance containing repository, Issue, mode, exact start SHA, run ID/attempt, and patch SHA-256. It cannot push or open a PR.

The publisher runs on a fresh runner and checkout. Before minting the App token it:

1. validates the structured result and exact provenance;
2. rechecks the open owner-authored Issue and trusted receipt;
3. verifies the expected branch/PR state and start SHA;
4. applies the patch with `git apply --check`; and
5. rejects protected paths.

The token is minted only after those checks. New work can create only `issue/<number>` and one draft PR. Revisions must fast-forward the same branch and PR; concurrent head changes fail instead of being overwritten. GitHub's published head SHA is verified before CI.

The Codex job runs with `permission-profile: :workspace` and `safety-strategy: drop-sudo`. No privileged secret is used after Codex in that job. Its output remains untrusted until the separate publisher validates it.

## Protected paths

The publisher and reusable CI always reject:

- inherited Issue forms;
- `.github/workflows/**`;
- `.github/actions/**`;
- root or nested `AGENTS.md`; and
- the central pipeline/reconciliation helpers and client workflow templates.

Client callers add repository-specific protected paths through `AGENT_PROTECTED_PATHS`. Application repositories should include Terraform, infrastructure, deployment-policy, migration, and other authority-bearing paths appropriate to that product. The infrastructure repository may deliberately allow infrastructure-as-code edits and credential-free format/validate/test checks, but it must not expose plan/apply or persistent credentials to the Issue pipeline.

Verifier or policy changes are manually supervised platform work. There is no label or Issue-text bypass.

## Review and merge

Deterministic CI runs on the exact published SHA before the initial draft becomes ready. Native automatic Codex review then provides an advisory P0/P1 pass. The pipeline never parses review prose and an AI conclusion cannot authorize merge.

The reusable owner-approval workflow accepts only a review submitted by the repository owner on an `issue/<number>` PR in the same repository and binds `atkandi/owner-approval` to the review's exact commit. New commits have no successful status until the owner approves that revision.

The publisher arms native auto-merge only when it can verify all of the following on the base branch:

- repository auto-merge is enabled;
- at least one approving review is required;
- stale reviews are dismissed;
- conversations must be resolved;
- strict required status checks include `atkandi/owner-approval`; and
- at least one additional deterministic check is required.

If protection cannot be read or enforced—currently including private repositories on the account's GitHub plan—the pipeline leaves a ready PR for manual owner merge. It never recreates branch protection in a weaker workflow.

## Infrastructure and deployment

Application repositories receive no cloud provisioning authority. Infrastructure Codex work may edit and locally validate IaC, but persistent/shared/production plan and apply remain separate trusted post-merge workflows. Apply requires explicit human authorization of the reviewed plan and its provenance. Prefer narrowly scoped OIDC credentials; keep any provider token out of implementation, publisher, review, and PR CI.

## Project boundary

The Project mirrors lifecycle labels and PR state. It may update membership and Status but not Priority, Waiting On, or unrelated human fields. Project changes cannot execute, publish, review, approve, merge, deploy, or broaden repository authority.
