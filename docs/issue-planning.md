# Issue planning

Use this guide while drafting and reviewing Issues, before implementation starts. An Issue is the human-reviewed contract for a unit of work; the execution pipeline begins only when an Implementation Issue is published with its prefilled `@codex` instruction.

## Choose the unit of work

- One Implementation Issue authorizes one repository-scoped Codex task and normally one draft pull request.
- Size an Implementation Issue as one cohesive, reviewable repository outcome—not as every internal coding step and not as an unrelated collection of changes.
- Combine tightly coupled work in the same repository when it should be implemented, reviewed, released, and rolled back together. Use acceptance-criteria checklists or planning subissues to retain useful detail without creating repetitive executable Issues and pull requests.
- Split work when parts belong to different repositories or are independently reviewable, releasable, or reversible.
- Do not make Codex infer whether several Issues should share a pull request. Decide the boundary during planning.

## Use parents and subissues

- Use a Planning / deferred parent for a larger outcome, especially one spanning repositories. The parent coordinates scope, decisions, dependencies, and progress; it does not authorize implementation and must not contain `@codex` execution instructions.
- Create an Implementation subissue for each separately authorized repository outcome or reviewable slice.
- Cross-repository work requires one executable Issue per repository. An application Issue cannot authorize infrastructure work, and an infrastructure Issue cannot authorize application work.
- When several same-repository details should produce one pull request, use one executable Implementation subissue for their combined outcome. Keep the remaining detail as checklists or non-executable planning subissues.
- A small single-repository change needs only one normal Implementation Issue; do not create a parent without a coordination need.

## Make the contract executable

Before publication, confirm the Issue records:

- the observable intended outcome;
- verifiable acceptance criteria;
- confirmed product, design, technical, or compatibility decisions;
- explicit out-of-scope boundaries;
- expected validation;
- likely documentation impact; and
- its parent or related Issues when applicable.

Prefer outcome and constraints over prescribing internal implementation details unless the implementation decision is already confirmed. Keep unresolved product decisions in Planning / deferred until they are settled.

## Publish deliberately

1. Draft and debate the Issue until you want the work to run.
2. Choose Implementation only for work that is ready to execute; otherwise choose Planning / deferred.
3. Publishing an Implementation Issue is the queue action. Project fields and labels provide visibility but do not authorize execution.
4. Codex implements only that Issue in that repository and normally opens one draft pull request with a completed Merge Brief.
5. Human pull-request review and merge remain the approval point for persistent real-world changes.

For the current rollout state and canary requirement, see [the transition runbook](transition.md).
