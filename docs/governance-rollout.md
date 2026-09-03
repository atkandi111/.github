# Governance and Portfolio lifecycle

The Portfolio Project is the canonical view of priority and status. It is never an execution or merge control surface.

## Status mapping

| State | Project Status |
| --- | --- |
| Planning/deferred, backlog, existing unstarted work, or disabled pipeline | `Todo` |
| Issue has the trusted `agent:authorized` receipt and no ready PR, or its PR has changes requested | `In Progress` |
| Open ready PR | `For Review` |
| Merged PR or Issue closed as completed | `Done` |

The reconciler is idempotent and edits only Status. It never edits Priority, Waiting On, or unrelated fields. Dragging a Project card, changing Status, editing text, or adding a label later cannot execute, publish, review, merge, or deploy anything.

The publisher opens one ready PR with a Merge Brief and verified SHA. Normal CI and optional native Codex review follow. The owner manually merges or requests changes; a valid changes-requested review updates the same PR.

## Portfolio membership

The Project's native auto-add rule covers D'EMAND. The scheduled account reconciler covers every repository in `config/portfolio-repositories.txt`:

- `scripts/reconcile-portfolio-project audit` reports membership and Status drift.
- `scripts/reconcile-portfolio-project reconcile` adds missing open Issues/PRs and repairs only Status.
- It never removes or archives items.

## Future repository onboarding

1. Add `OWNER/REPOSITORY` to `config/portfolio-repositories.txt` through a reviewed central PR.
2. Run `./client-setup onboard TARGET atkandi111/.github OWNER/REPOSITORY` and tailor CI.
3. Create the three labels with `./client-setup labels OWNER/REPOSITORY`.
4. Configure the OpenAI key, publisher App, protected paths, and disabled pipeline variable.
5. Merge the thin caller PR manually and verify Project membership.
6. Optionally enable native Codex review, then enable the pipeline and observe the first real low-risk Issue.

Missing labels, credentials, caller, or Project coverage mean onboarding is incomplete. Never compensate by trusting Issue text or Project state.
