# Security and trust boundaries

## Authorization

New work is authorized only by the original GitHub `issues.opened` event when the repository owner authored and opened the Issue, its initial labels contain `implementation`, and they do not contain `planning`.

Intake records `agent:authorized` as a machine-issued receipt. Owner revisions and manual retry require that receipt. Later labels, Issue/PR text, comments, Project fields, similar wording, and other actors never authorize new work. Closing the Issue stops publication. `AGENT_PIPELINE_ENABLED` is the disabled-by-default kill switch.

## Queue and retry

GitHub Actions `queue: max` runs one Issue at a time per repository and retains up to 100 waiting runs. Repositories have independent queues. Waiting-time FIFO is sufficient; Issue numbers do not imply dependency order.

An owner-only manual dispatch retries a previously authorized Issue. It reuses the existing `issue/<number>` branch and open PR when present. There is no automatic retry loop or separate attempt controller. Runs beyond GitHub's queue capacity remain visible as canceled, unexecuted work and require the same explicit retry.

## Credential separation

| Boundary | Credentials and authority |
| --- | --- |
| Intake | Repository `GITHUB_TOKEN` for Issue labels and Issue/PR metadata; no publisher or production credential. |
| Codex | Contents, Issues, and PR read plus a dedicated non-production OpenAI key through the official Codex Action. No GitHub write, publisher, Project, deployment, or infrastructure credential. |
| Clean publisher | One-hour GitHub App token limited to the current repository with Contents, Issues, and Pull requests write. No OpenAI, Administration, Project, deployment, or cloud credential. |
| Normal PR CI | Contents read only; no secret, OIDC, deployment, or persistent-infrastructure authority. |
| Portfolio reconciliation | Central Project token; may add items and update Status only. It never reaches implementation or publishing. |

The App token is required because publication must trigger normal PR automation without giving Codex write credentials. There is no PAT or repository `GITHUB_TOKEN` publishing fallback.

## Artifact and publisher boundary

Codex edits an isolated checkout and emits only structured Merge Brief data, a binary-capable Git patch, and provenance containing repository, Issue, mode, exact start SHA, run ID/attempt, and patch SHA-256.

On a fresh runner, the publisher validates the result and provenance, rechecks the open owner-authored Issue and receipt, verifies the expected branch/PR and start SHA, applies the patch with `git apply --check`, and rejects protected paths. Only then does it mint the App token.

The publisher creates or updates only `issue/<number>` and one ready PR. Concurrent head changes fail instead of being overwritten, and the published SHA is verified. Owner changes-requested reviews must target that exact SHA; their summary and associated inline comments become untrusted revision input.

The Codex job uses `permission-profile: :workspace` and `safety-strategy: drop-sudo`. No privileged secret is used after Codex in that job. Its output remains untrusted until validation.

## Protected paths

The publisher and reusable CI reject inherited Issue forms, `.github/workflows/**`, `.github/actions/**`, root or nested `AGENTS.md`, central pipeline/reconciliation helpers, and client workflow templates. Client callers add product-specific patterns through `AGENT_PROTECTED_PATHS`.

Application repositories should protect infrastructure, deployment policy, migrations, and other authority-bearing paths. The infrastructure repository may allow credential-free IaC edits and validation, but not plan/apply credentials.

## Review, merge, and deployment

Normal PR CI runs after publication. Native Codex review is an optional advisory repository setting. The pipeline neither invokes nor parses it.

The repository owner reviews the Merge Brief, diff, CI, and any review findings, then manually merges or requests changes. There is no synthetic approval status or automatic merge.

Application repositories receive no cloud provisioning authority. Persistent/shared/production plan, apply, and deployment remain separate trusted post-merge workflows with explicit human authorization and appropriately scoped credentials, preferably OIDC.

## Project boundary

The Project may mirror the authorization receipt and ordinary Issue/PR state into Status. It never edits Priority, Waiting On, or unrelated human fields, and cannot execute, publish, review, merge, deploy, or broaden authority.
