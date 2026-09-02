# Issue planning

Use this guide while drafting and reviewing Issues. An owner-created **Implementation issue** is the executable contract and is queued automatically from its original form-applied label. **Planning / deferred** is the explicit non-executable opt-out.

## Choose the unit of work

- One executable Issue authorizes one repository-scoped run, one `issue/<number>` branch, and normally one pull request.
- Use one cohesive, reviewable repository outcome—not every coding step and not an unrelated bundle.
- Combine tightly coupled same-repository details when they should be implemented, reviewed, released, and rolled back together. Use acceptance checklists or non-executable planning subissues to retain detail without creating repetitive PRs.
- Split work when parts belong to different repositories or are independently reviewable, releasable, or reversible.
- A small single-repository change needs one normal Implementation Issue; do not add a parent without a coordination need.

## Parents, subissues, and cross-repository work

- Use a Planning / deferred parent for a larger outcome, especially one spanning repositories. It coordinates scope, decisions, dependencies, and progress but never authorizes implementation.
- Create one executable Issue per repository. An application Issue cannot authorize infrastructure work, and an infrastructure Issue cannot authorize application work.
- When several same-repository details should produce one PR, use one Implementation subissue for their combined outcome and keep the rest as checklists or planning subissues.
- Before parallel cross-repository work, stabilize an integration contract covering ownership, interfaces/schemas, exact environment variables, secrets/outputs, errors, retries, idempotency, deployment order, rollback, and validation. Copy the relevant parent URL and revision into every executable subissue and Merge Brief.

## Make the contract executable

Before publication, confirm the Issue records:

- the observable intended outcome;
- verifiable acceptance criteria;
- confirmed product, design, technical, or compatibility decisions;
- explicit out-of-scope boundaries;
- expected validation;
- likely documentation impact;
- dependencies and overlapping touchpoints;
- its parent or related Issues; and
- the reviewed integration-contract revision when cross-repository work is involved.

Keep unresolved product decisions in Planning / deferred. Prefer outcomes and constraints over prescribing internals unless a technical choice is already settled.

## Publish deliberately

1. Draft and debate the Issue until you want it to run.
2. Choose **Implementation issue** only for ready work. When the repository owner publishes it, the initial `implementation` label queues it without a second approval step.
3. Choose **Planning / deferred issue** for backlog, unresolved work, or a coordination-only parent. Its initial `planning` label never queues implementation.
4. Do not add `@codex implement`. Native Cloud execution is a separate path and would risk duplicate work.
5. Issue text, comments, edited text, Project fields, and labels added after creation cannot authorize execution. Existing open Issues are not bulk-triggered.
6. The repository queue runs one Issue at a time, retains up to 100 waiting runs through `queue: max`, and allows different repositories to run in parallel. Waiting-time FIFO is sufficient; Issue-number order is not guaranteed.
7. The pipeline publishes one draft PR, completes the Merge Brief, runs deterministic CI, and makes the initial revision ready for native Codex and owner review.
8. Owner-requested changes update the same PR. CI reruns and old approval cannot apply to the new SHA. A fresh Codex review is optional because it is advisory.
9. Owner approval of the current revision is the merge authorization. GitHub auto-merges only where enforceable repository protection is available; otherwise the owner merges manually.

## Dependencies and overlap

- The automated queue serializes all work in a repository, so it avoids simultaneous Issue-generated PRs there. Different repositories remain independent.
- A dependent Issue should still be created only after its predecessor is merged and `main` CI is green, because queue order is not dependency inference.
- If a human product branch overlaps the queue, pause new implementation by setting `AGENT_PIPELINE_ENABLED=false`, finish or coordinate the existing branch, then re-enable it.
- A canceled run beyond GitHub's 100-pending capacity is unexecuted work. It remains visible as a canceled run and requires explicit owner recovery; it must never be treated as completed.

The Portfolio Project is status and priority only. Moving an item does not queue, revise, approve, merge, or deploy anything.
