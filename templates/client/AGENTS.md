# Agent instructions

Read `PROJECT.md` before implementation. The Issue defines the requested scope; do not invent missing product intent.

## Repository map

Document the important application directories here.

## Commands

- Build: document the command or `not applicable`.
- Test: document the command or `not applicable`.
- Lint: document the command or `not applicable`.
- Typecheck: document the command or `not applicable`.

## Engineering rules

- Follow KISS: choose the smallest, simplest safe implementation that satisfies the Issue. Reuse existing patterns and avoid speculative abstractions.
- Do not introduce a new runtime dependency, external service, or architectural layer without explicit human authorization. Prefer existing tooling and report any new development-only dependency.
- Name human-created branches `<type>/<short-kebab-scope>`, where `<type>` is `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, or `chore`. Pipeline-created branches use `issue/<number>-attempt-<number>`. Do not use author or tool names as prefixes.
- Use Conventional Commit subjects such as `feat(scope): add export controls`. Do not rewrite history or force-push unless explicitly requested.

## Done

Keep changes within the Issue, add appropriate tests, run applicable checks, and report assumptions. If a meaningful user-visible or product decision is unspecified, stop with `HUMAN INPUT REQUIRED` and state the missing decision.
