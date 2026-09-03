# Atkandi developer platform

This public account-level `.github` repository owns the portfolio's shared Issue-to-PR pipeline, Codex policy, deterministic CI, Project synchronization, and default Issue/PR templates.

## Human summary

The solo-developer workflow has two attention points:

1. Carefully prepare and publish an **Implementation issue** when work is ready. Publishing queues it automatically. Use **Planning / deferred** when it should not run.
2. Review the resulting pull request. Request changes on the same PR or click **Merge** when satisfied.

The pipeline handles the middle: one repository-scoped run, one `issue/<number>` branch, one ready PR, and a completed Merge Brief. Normal PR CI and optional native Codex review then run. The Project mirrors status only.

Manual merge is the human approval boundary.

Do not add `@codex implement` to an Issue. That starts a separate native Cloud task and can duplicate the Actions-hosted run.

## Architecture

| Part | Responsibility |
| --- | --- |
| Implementation Issue | Reviewed repository-scoped contract; the owner's initial `implementation` label authorizes one run. |
| Planning / deferred Issue | Backlog, unresolved planning, or coordination parent; never executable. |
| Repository queue | Runs one Issue at a time per repository with `queue: max`; repositories run independently. |
| Codex job | Edits an isolated checkout without GitHub write, publisher, deployment, or production credentials. |
| Clean publisher | Validates the patch in a fresh checkout, then uses a short-lived repository-scoped GitHub App token to push and open/update one PR. |
| Normal PR CI | Verifies the published revision without deployment credentials. |
| Native Codex review | Optional advisory review controlled by the repository's Codex setting. |
| Portfolio Project | Mirrors Todo, In Progress, For Review, and Done; it cannot authorize work. |
| Trusted post-merge workflows | Own deployment and persistent/shared infrastructure effects separately. |

## Normal flow

1. The owner publishes an Issue using the inherited **Implementation issue** form. Its original event must contain `implementation` and not `planning`.
2. Intake records `agent:authorized`. Later text, comments, labels, and Project fields cannot authorize a run.
3. Codex reads the Issue as untrusted data and produces a patch, structured result, and provenance.
4. A fresh publisher rechecks the Issue, receipt, start SHA, patch hash, branch/PR state, and protected paths before minting its App token.
5. It creates or updates `issue/<number>` and one ready PR, verifies the GitHub head SHA, and completes the Merge Brief.
6. Normal PR CI and optional Codex review run.
7. An owner changes-requested review for the exact current SHA queues one revision using the review summary and inline comments. The same PR is updated.
8. The owner manually merges the accepted revision. An owner-only dispatch can retry previously authorized work after an operational failure.

## Centralized pieces

- `policy/AGENTS.md`: shared implementation and review rules.
- `.github/workflows/agent.yml`: reusable authorization, implementation, and clean publication.
- `.github/workflows/ci.yml`: reusable credential-free CI and protected-path gate.
- `.github/workflows/portfolio-project.yml`: scheduled membership and lifecycle reconciliation.
- `.github/ISSUE_TEMPLATE/` and `.github/pull_request_template.md`: account defaults where repositories do not override them.
- `templates/client/`: thin callers and repository guidance skeletons.
- `client-setup`: conservative installer, release-pin checker, and label setup command.

Client callers follow `atkandi111/.github@main`, so reviewed central updates propagate without copying their implementation. Thin local callers remain necessary because account-level `.github` repositories do not inherit Actions workflows.

## Trust boundaries

- `AGENT_PIPELINE_ENABLED` is the disabled-by-default kill switch.
- `OPENAI_API_KEY` belongs to a dedicated non-production project. The Codex job receives no GitHub write credential.
- `PUBLISHER_APP_PRIVATE_KEY` is used only by the clean publisher. Its installation token is short-lived and limited to one repository with Contents, Issues, and Pull requests write access.
- Workflow/action paths, Issue forms, pipeline helpers, and every `AGENTS.md` are protected from Issue-driven publication. Client repositories add product-specific protected paths.
- Pull-request CI receives no deployment or persistent-infrastructure secret. Production/shared effects remain separate post-merge work.
- Neither AI output nor Project state can publish, approve, merge, or deploy.

## Adoption

```bash
./client-setup onboard /path/to/repository atkandi111/.github OWNER/REPOSITORY
./client-setup check /path/to/repository
```

Create the three required labels, configure the dedicated OpenAI key and publisher App, keep the pipeline disabled while merging the reviewed caller PR, then enable it. See [setup](docs/cloud-setup.md), [security](docs/security.md), [release and rollback](docs/release.md), and [Issue planning](docs/issue-planning.md).
