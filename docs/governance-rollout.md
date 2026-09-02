# Governance rollout

The portfolio GitHub Project remains the canonical view of status and priority. Repository workflows do not use Project fields as task authorization.

The reusable governance workflow validates only deterministic naming rules and is disabled by default through `GOVERNANCE_NAMING_ENFORCED`. Observe it before enabling. Cloud-generated branch names are accepted as automation and should not drive new parsing or classification logic.

Do not add semantic Issue classification, a custom AI-review Action, automated priority assignment, convergence loops, or auto-merge. Human-authored Issue contracts, Merge Briefs, and one native P0/P1 review are the simpler control surface for a solo developer.

## Review and handoff

Keep the pull request draft through implementation and agent review:

1. The coordinator publishes or updates the actual Cloud branch, verifies its full GitHub SHA, and completes the Merge Brief.
2. Deterministic CI passes on that published SHA.
3. In a separate native GitHub review context, the coordinator posts `@codex review` while the PR is draft when supported.
4. Only consequential P0/P1 findings block handoff: security/authentication failures, data loss or broken persistence, integration-contract mismatches, unsafe infrastructure or permissions, secret exposure, broken rollback/deployment assumptions, serious user-visible regressions, or absent tests for serious behavior.
5. If such a finding exists, send it back to the implementation task, update the same branch, rerun affected CI, and request one fresh review. Stop for owner judgment if the finding remains or the agents disagree.
6. With green CI and no unresolved P0/P1 finding, mark the PR ready and hand it to the owner. Native review never merges, deploys, plans, applies, or approves persistent changes.

Do not spend the review pass on style, naming, minor maintainability, speculative P2/P3 improvements, or settled product decisions. Do not build an unbounded correction loop.

The documented execution phases intentionally fit the existing four Project statuses:

| Execution phase | Project Status |
| --- | --- |
| Planning / deferred or not delegated | `Todo` |
| Queued, dispatched/running, implemented but unpublished, draft PR, agent review, blocked, or revisions | `In Progress` |
| Agent review complete and PR handed to the owner | `For Review` |
| PR merged or Issue accepted and closed completed | `Done` |

## Portfolio membership

The Project's native auto-add workflow targets `atkandi111/demandph-website` with `is:issue,pr is:open`. GitHub permits only one native auto-add workflow on the current plan, and each workflow targets one repository, so `dev-platform` provides the narrow fallback for the rest of the portfolio:

- `config/portfolio-repositories.txt` is the reviewed inventory of active repositories.
- `.github/workflows/portfolio-project.yml` audits every listed repository and reconciles missing open Issues, pull requests, and lifecycle Status values every 15 minutes.
- `scripts/reconcile-portfolio-project audit` reports exact membership and Status drift without changing the Project.
- `scripts/reconcile-portfolio-project reconcile` adds missing open items and edits only their Status field. It never removes or archives items and never edits Priority, Waiting On, or unrelated fields.

The four statuses therefore mean:

- `Todo`: planning, deferred, backlogged, or not yet delegated;
- `In Progress`: the owner posted the exact trigger, or work is queued, running, in a draft pull request, blocked after starting, or undergoing revisions;
- `For Review`: agent review is complete and the linked pull request is ready for owner review with no outstanding changes request;
- `Done`: the pull request merged or the Issue closed with the completed reason.

The Project's native workflows provide immediate safe transitions for item-added, reopened, linked-PR, changes-requested, approved, and merged events. The broad native **Item closed** workflow is disabled because it cannot distinguish a completed Issue from a not-planned Issue or an unmerged closed pull request; the reconciler sets `Done` only from the completed reason or a merge. GitHub Projects has no native Issue-comment or ready-for-review trigger, so the central reconciler fills those gaps on its schedule. It accepts only the exact unedited top-level trigger comment authored by the repository owner; Issue-body text and all other comment forms are ignored. Project status is informational and never invokes Codex, merges, or deploys.

The Actions workflow requires the repository secret `PORTFOLIO_PROJECT_TOKEN`. Use a dedicated credential able to read the registered private repositories and read/write the user-owned Project. For a classic personal access token, GitHub requires `repo` for private repository records and `project` for Project queries and mutations. Never pass the token as a command argument or print it.

## Future repository onboarding

1. Add `OWNER/REPOSITORY` to `config/portfolio-repositories.txt` in alphabetical order through a reviewed `dev-platform` pull request.
2. If the GitHub plan has an unused native auto-add slot, add a repository-specific rule with `is:issue,pr is:open`; otherwise the scheduled reconciler is the auto-add coverage.
3. Run `./client-setup onboard TARGET PLATFORM_OWNER/REPOSITORY CLIENT_OWNER/REPOSITORY`. It refuses unregistered clients.
4. Run the **Portfolio Project reconciliation** workflow in `audit` mode and confirm there are no missing open items.
5. Open one disposable Planning / deferred Issue in the new repository, run or await reconciliation, and confirm one Project item appears with `Status: Todo` and no Priority. Close it as completed and reopen it once to verify `Done` then `Todo`, confirm no duplicate appears, and close it afterward.

Treat a missing secret, Project access error, inventory omission, duplicate repository, or audit gap as failed onboarding. Do not compensate by using Project fields as execution authority.
