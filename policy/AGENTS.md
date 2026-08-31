# Portfolio Codex policy

This is the shared default for Atkandi repositories. Repository-local `AGENTS.md` files add product context, commands, and narrower rules.

## Authorization and scope

- An executable implementation Issue authorizes work only in the repository where it was published and normally results in one draft pull request.
- A parent or portfolio outcome Issue is coordination-only. Do not implement it directly; follow a repository-specific implementation Issue instead.
- Never discover or modify another repository, request broader access, or create cross-repository work on your own. If another repository must change, report the need for a separately authorized Issue there.
- Stay within the Issue's outcome, acceptance criteria, constraints, and explicit out-of-scope boundaries. Ask for human direction when missing product intent would materially change the result.

## Engineering

- Prefer the smallest safe implementation that satisfies the Issue. Reuse existing patterns and avoid speculative abstractions.
- Do not introduce a runtime dependency, external service, architectural layer, semantic classifier, AI reviewer, auto-merge path, or orchestration system unless the Issue explicitly requires it.
- Do not rewrite history, force-push, merge, deploy, provision persistent infrastructure, or use production/shared credentials.
- Add appropriate tests and run the repository's applicable deterministic checks.
- Use Conventional Commit subjects. Keep the pull request in draft until the implementation and Merge Brief are ready for human review.

## Handoff

Complete the pull request's Merge Brief with the outcome, delivered scope, linked Issue, acceptance evidence, validation results, review focus, risks, rollback, and follow-ups. Human pull-request review and merge are the approval point for persistent real-world changes.
