# Central agent policy

`governance/AGENTS.md` is the reviewed portfolio baseline. Managed runs receive
the promoted baseline from the reusable workflow, so client repositories keep
only a small local `AGENTS.md` overlay.

## Context budgets

- Central baseline: 4 KiB maximum.
- Repository-root overlay: 4 KiB maximum.
- Effective central plus root context: 8 KiB maximum.
- Nested overlay: 2 KiB maximum per file.

Generated instruction blocks count toward these limits. Local overlays should
contain only repository commands, project-specific safety gates, and pointers
to focused context. They must not copy the central baseline or weaken it.

## Promotion

1. Edit `governance/AGENTS.md` and keep the change independently reviewable.
2. Run `python3 scripts/sync-agent-policy.py` to update the generated workflow
   block, then run `./tests/run.sh`.
3. Canary the exact candidate SHA using `docs/release.md` and record evidence on
   the pull request.
4. Merge only after review. Normal clients load the promoted baseline on their
   next newly started managed run through `@main`.

Already-running sessions keep the policy they started with and must restart to
receive a promoted revision. Unreviewed source edits do not propagate because
CI rejects a workflow block that differs from the canonical file.

## Rollback

Disable new managed runs, prepare a reviewed revert, regenerate the workflow
block, canary the exact revert SHA, merge it, and then re-enable the pipeline.
Do not rewrite `main`.
