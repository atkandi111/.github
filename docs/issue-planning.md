# Issue planning

Use this guide while drafting and reviewing Issues. An Implementation Issue is the human-reviewed contract for ready work and is queued by the coordinator by default. GitHub publication alone does not start Codex; the coordinator immediately posts the proven owner-only top-level trigger. Planning / deferred is the explicit opt-out.

## Choose the unit of work

- One Implementation Issue authorizes one repository-scoped Codex task, one issue-specific branch, and normally one draft pull request.
- Size an Implementation Issue as one cohesive, reviewable repository outcome—not as every internal coding step and not as an unrelated collection of changes.
- Combine tightly coupled work in the same repository when it should be implemented, reviewed, released, and rolled back together. Use acceptance-criteria checklists or planning subissues to retain useful detail without creating repetitive executable Issues and pull requests.
- Split work when parts belong to different repositories or are independently reviewable, releasable, or reversible.
- Do not make Codex infer whether several Issues should share a pull request. Decide the boundary during planning.

## Sequence dependencies and overlap

- Keep no more than 2–3 independent implementations active per repository initially. This is an operating recommendation, not another automated queue.
- Independent Issues may run in parallel on separate branches and PRs.
- A functionally dependent Issue waits until its predecessor is merged and post-merge `main` CI is green. Normally serialize work likely to touch the same sensitive or overlapping code the same way.
- A finished Cloud task without a verified draft PR still occupies its active slot and does not satisfy a dependency.
- If overlap runs accidentally, merge one PR first, update the other from current `main`, resolve semantic conflicts, and rerun CI and independent review. Do not make stacked PRs the default.

## Use parents and subissues

- Use a Planning / deferred parent for a larger outcome, especially one spanning repositories. The parent coordinates scope, decisions, dependencies, and progress; it does not authorize implementation and must not contain `@codex` execution instructions.
- Create an Implementation subissue for each separately authorized repository outcome or reviewable slice.
- Cross-repository work requires one executable Issue per repository. An application Issue cannot authorize infrastructure work, and an infrastructure Issue cannot authorize application work.
- When several same-repository details should produce one pull request, use one executable Implementation subissue for their combined outcome. Keep the remaining detail as checklists or non-executable planning subissues.
- A small single-repository change needs only one normal Implementation Issue; do not create a parent without a coordination need.

Before dispatching cross-repository subissues in parallel, stabilize a reviewed integration contract in the parent. Cover ownership, APIs or events, schemas, exact environment-variable names and semantics, secret ownership, infrastructure outputs, errors, retries, idempotency, deployment order, rollback, and integration validation. Copy the relevant contract into each subissue because a repository-scoped task must not discover another repository. Identify it by parent URL and revision in every subissue and Merge Brief. Record amendments in the parent and propagate them explicitly; agents must not negotiate incompatible interfaces independently. If infrastructure discovery determines the interface, finish that discovery first. Close the parent only after subissues, rollout steps, and integration validation complete.

## Make the contract executable

Before publication, confirm the Issue records:

- the observable intended outcome;
- verifiable acceptance criteria;
- confirmed product, design, technical, or compatibility decisions;
- explicit out-of-scope boundaries;
- expected validation;
- likely documentation impact; and
- dependencies and likely overlapping touchpoints;
- its parent or related Issues when applicable; and
- the parent URL and integration-contract revision for cross-repository work.

Prefer outcome and constraints over prescribing internal implementation details unless the implementation decision is already confirmed. Keep unresolved product decisions in Planning / deferred until they are settled.

## Publish deliberately

1. Draft and debate the Issue until you want the work to run.
2. Choose Implementation only for ready work. The coordinator creates it and immediately queues it without seeking another approval. Choose Planning / deferred when it must not run.
3. The repository owner queues the Implementation Issue with this exact new top-level comment: `@codex implement this issue in this repository. Open one draft pull request and complete its Merge Brief.`
4. Issue-body text, quoted or edited text, other actors, Project fields, and labels do not authorize execution.
5. If the coordinator cannot post as the repository owner, the trigger is the owner's one remaining manual step; leave the Issue in `Todo` until then.
6. Codex implements only that Issue in that repository on one issue-specific branch.
7. When Cloud finishes, the coordinator uses native **Create PR/Update PR**, confirms the PR is draft, completes its Merge Brief, and verifies the published head SHA. Until then, the task is not operationally complete.
8. After deterministic CI, the coordinator requests one separate native `@codex review`. Only consequential P0/P1 findings block owner handoff; one correction and fresh review are allowed before unresolved questions go to the owner.
9. Human pull-request review and merge remain the approval point for persistent real-world changes.

For the current rollout state and canary requirement, see [the transition runbook](transition.md).
