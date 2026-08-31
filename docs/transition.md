# One-pass transition runbook

This runbook assumes the former custom pipeline has no production users. Keep existing product branches and pull requests intact; the transition changes the work-entry and verification path, not product history.

## Merge order

1. Merge the `dev-platform` transition first. Run `./tests/run.sh` and confirm reusable workflow access is still enabled for the private client repositories.
2. Merge each client transition. Re-run its pull-request checks after `dev-platform@main` contains the new workflow contract.
3. In each Codex Cloud environment, grant only that repository, install `policy/AGENTS.md` using `docs/cloud-setup.md`, and add no deployment or infrastructure credential.
4. Run one disposable low-risk Issue-to-draft-PR canary. Do not depend on initial-body mention behavior until this passes.
5. After the canary, remove the obsolete `OPENAI_API_KEY` secret and `AGENT_*` / `PIPELINE_*` variables from repositories that had the former pipeline. Remove the old `agent` label when no historical workflow depends on it.
6. Require the deterministic CI check on protected `main` branches. Keep production environments and infrastructure apply approvals separate.

## Existing unmerged work

- Continue existing product branches and pull requests; do not rebase, regenerate, or restart them merely for this transition.
- Review and merge them normally. Add the Merge Brief headings when doing so improves the handoff, but do not block an otherwise ready PR on mechanical template migration.
- If an old pipeline-generated draft PR exists, treat it as an ordinary draft PR. Its Issue remains context, but the removed workflow will not retry or publish another attempt.

## Existing Issues

- Do not bulk-edit or trigger open Issues.
- Existing backlog and parent/outcome Issues remain coordination records. They never become executable merely because they are in the portfolio Project or carry an old label.
- When an existing repository Issue is ready to execute, confirm that it has an intended outcome, acceptance criteria, constraints, and out-of-scope section, then add one `@codex implement this issue...` instruction. That explicit action puts it in the queue.
- A cross-repository Issue should become a parent outcome with one separately authorized implementation Issue in each affected repository. Link them with subissues or checklist links.

## New Issues

- Use **Implementation issue** when publishing should immediately enqueue one repository-scoped Codex task and normally one draft PR.
- Use **Backlog or human change** when publication should not start Codex.
- Use **Portfolio outcome** only for coordination across repositories. It never includes an execution mention.
- Keep status and priority in the existing portfolio GitHub Project. Project fields do not grant authority.

## Rollback

If the canary exposes a Codex Cloud limitation, stop publishing implementation Issues or omit the `@codex` line. Continue manual development and centralized CI. Revert the platform release only when the shared verifier itself is faulty; do not restore the custom runner/publisher as a reflex.
