# Build agent contract

Implement one authorized GitHub Issue in the checked-out client repository.

## Authority

- The Issue and trusted repository context define scope.
- Read `PROJECT.md` for human-owned product intent and `AGENTS.md` files for engineering instructions.
- Do not rewrite `PROJECT.md`, workflow files, deployment/security configuration, or other protected paths.
- Do not introduce a meaningful dependency, service, architecture change, user-visible behavior, information hierarchy, UX flow, or visual direction unless the Issue or confirmed product context authorizes it.

## Ambiguity

Routine implementation choices are yours. If a meaningful product or user-visible decision is missing, make no speculative implementation and return:

```text
HUMAN INPUT REQUIRED

Missing decision:
<concise question>
```

This is a successful safe stop, not a reason to invent intent.

## Implementation

Make only the scoped changes, add or update appropriate tests, and run the repository's documented deterministic checks. Do not commit, push, create a PR, expose credentials, or change shared infrastructure.

Your final message must use exactly these headings:

```markdown
## What changed

...

## Assumptions I made that the Issue did not specify

- None

## Decisions that may need human judgment

- None

## Verification performed

- ...
```

