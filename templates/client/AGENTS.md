# Repository instructions

Read `PROJECT.md` and the authorized Issue before editing. The central Atkandi policy is mandatory; this file adds only repository-specific context.

## Repository map

Document only the directories an agent must know before making a safe change.

## Commands

- Build: document the command or `not applicable`.
- Test: document the command or `not applicable`.
- Lint/typecheck: document the commands or `not applicable`.

## Engineering rules

- Follow KISS: make the smallest safe change, reuse existing patterns, and avoid speculative abstractions.
- Do not add a new runtime dependency, external service, or architectural layer without authorization. Prefer existing tooling and report any new development-only dependency.
- Name human-created branches `<type>/<short-kebab-scope>`, where `<type>` is `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, or `chore`. Pipeline-created branches use `issue/<number>-attempt-<number>`. Do not use author or tool names as prefixes.
- Use Conventional Commit subjects such as `feat(scope): add export controls`. Do not rewrite history or force-push unless explicitly requested.

## Done

Add only essential project-specific safety gates here. Run applicable checks and report assumptions and verification.
