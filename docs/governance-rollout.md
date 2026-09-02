# Governance and Portfolio lifecycle

The Portfolio Project is the canonical view of priority and status. It is never an execution or merge control surface.

## Execution lifecycle

| Execution phase | Project Status |
| --- | --- |
| Planning / deferred, backlog, existing unstarted work, or disabled pipeline | `Todo` |
| Authorized/queued Issue, implementation, unpublished result, draft PR, failed CI, blocked work, or owner-requested revision | `In Progress` |
| Published PR is ready for owner review | `For Review` |
| PR merged or Issue accepted and closed as completed | `Done` |

The intake workflow adds `agent:authorized` as the durable execution receipt and `agent:in-progress` while a run or revision is active. Draft/ready state and changes-requested reviews supply the remaining lifecycle signals. The reconciler is idempotent and edits only Status. It never edits Priority, Waiting On, or unrelated fields.

Dragging a Project card, changing Status, adding a label later, or writing Issue text does not execute Codex, publish a branch, approve, merge, or deploy.

## Review and owner handoff

1. The clean publisher opens a draft PR with the Merge Brief and verified SHA.
2. Deterministic credential-free CI runs on that SHA.
3. Green CI makes the initial PR ready and removes `agent:in-progress`.
4. Native automatic Codex review provides an advisory P0/P1 pass when enabled.
5. The owner reviews the Merge Brief, diff, CI, and findings.
6. A changes-requested review sets the work back to In Progress and queues a bounded revision on the same PR.
7. Owner approval of the current SHA publishes `atkandi/owner-approval`. Native auto-merge may complete only when verified branch protection also requires deterministic CI, stale-review dismissal, and resolved conversations.

Do not parse Codex prose, create an AI approval status, auto-prioritize, or add a convergence loop. A fresh Codex review after a revision is optional because the owner and deterministic checks remain authoritative.

## Portfolio membership

The Project's one native auto-add rule covers `atkandi111/demandph-website` with `is:issue,pr is:open`. The account `.github` scheduled reconciler covers the rest of the reviewed inventory every 15 minutes:

- `config/portfolio-repositories.txt` lists active repositories.
- `.github/workflows/portfolio-project.yml` runs audit or reconciliation.
- `scripts/reconcile-portfolio-project audit` reports membership and Status drift.
- `scripts/reconcile-portfolio-project reconcile` adds missing open Issues/PRs and repairs only Status.

The reconciler never removes or archives items. Closed-not-planned Issues and unmerged closed PRs are not forced to Done.

## Future repository onboarding

1. Add `OWNER/REPOSITORY` to `config/portfolio-repositories.txt` in alphabetical order through a reviewed account `.github` PR.
2. Run `./client-setup onboard TARGET atkandi111/.github OWNER/REPOSITORY` and tailor CI commands.
3. Run `./client-setup labels OWNER/REPOSITORY` before relying on the inherited forms.
4. Configure the dedicated OpenAI key, publisher App installation/key, and disabled-by-default variables from `docs/cloud-setup.md`.
5. Merge the thin caller PR manually; verify account-default Issue/PR templates and Portfolio membership.
6. Enable native Codex automatic review.
7. Verify branch protection. Enable automatic merge only when the full native gate is enforceable; otherwise retain manual merge.
8. Set `AGENT_PIPELINE_ENABLED=true` and observe the first real low-risk Implementation Issue end to end.

Treat a missing label, secret, App installation, Project permission, caller, protection rule, or audit gap as failed onboarding. Do not compensate by trusting Issue text or Project state.
