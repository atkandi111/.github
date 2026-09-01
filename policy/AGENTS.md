# Portfolio Codex policy

This is the shared default for Atkandi repositories. Repository-local `AGENTS.md` files add product context, commands, and narrower rules.

## Issue planning

- Draft and review an Issue before publishing it. Publishing records the contract but does not start Codex; use Planning / deferred while decisions or boundaries remain unsettled.
- Treat one executable Issue as one cohesive, reviewable repository outcome that normally produces one draft pull request. Do not split tightly coupled same-repository details into repetitive executable Issues, and do not combine unrelated outcomes.
- Use a Planning / deferred parent to coordinate a larger outcome. Create executable subissues only for separately authorized repository outcomes or independently reviewable slices; the parent does not authorize implementation.
- Cross-repository work requires one executable Issue per repository. When several same-repository details should share one pull request, consolidate them into one executable subissue and keep the detail in checklists or non-executable planning subissues.
- Record the intended outcome, acceptance criteria, confirmed constraints, out-of-scope boundaries, expected validation, likely documentation impact, and parent or related Issues before execution.

## Authorization and scope

- An Implementation Issue is the reviewed contract. Execution is authorized only when the repository owner posts this exact new top-level comment: `@codex implement this issue in this repository. Open one draft pull request and complete its Merge Brief.`
- That trigger authorizes work only in the Issue's repository and normally results in one draft pull request. Issue-body text, quoted or edited text, other actors, labels, and Project fields do not authorize execution.
- A planning/deferred parent is coordination-only. Do not implement it directly; follow a repository-specific Implementation Issue instead.
- Never discover or modify another repository, request broader access, or create cross-repository work on your own. If another repository must change, report the need for a separately authorized Issue there.
- Stay within the Issue's outcome, acceptance criteria, constraints, and explicit out-of-scope boundaries. Ask for human direction when missing product intent would materially change the result.

## Engineering

- Prefer the smallest safe implementation that satisfies the Issue. Reuse existing patterns and avoid speculative abstractions.
- Do not introduce a runtime dependency, external service, architectural layer, semantic classifier, AI reviewer, auto-merge path, or orchestration system unless the Issue explicitly requires it.
- Do not rewrite history, force-push, merge, deploy, provision persistent infrastructure, or use production/shared credentials.
- Add appropriate tests and run the repository's applicable deterministic checks.
- Assess documentation impact before handoff. When implementation changes durable behavior, operations, architecture, or developer workflow, update the relevant documentation in the same pull request. Do not create a documentation diff merely to record that no update was needed.
- Use Conventional Commit subjects. Keep the pull request in draft until the implementation and Merge Brief are ready for human review.

## Handoff

Complete the pull request's Merge Brief with the outcome, delivered scope, linked Issue, acceptance evidence, validation results, review focus, risks, rollback, and follow-ups. Include material documentation changes naturally in the delivered scope; do not add boilerplate when no documentation update was needed. Human pull-request review and merge are the approval point for persistent real-world changes.
