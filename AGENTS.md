# Repository instructions

This repository is the reviewed source for portfolio-wide Codex guidance, reusable deterministic CI, governance checks, and client templates. It does not execute or publish implementation work in client repositories.

## Before editing

- Read `README.md` and the relevant document under `docs/`.
- Before creating, splitting, combining, or reviewing Issues, read `docs/issue-planning.md`.
- Keep the system lean enough for one developer to understand and maintain.
- Extend existing templates and reusable workflows before adding another abstraction.
- Treat changes under `policy/`, `templates/`, and reusable workflows as portfolio-wide changes.

## Trust boundaries

- An Implementation Issue is the reviewed contract and the default ready-work path. The coordinator posts the repository owner's exact supported top-level `@codex implement...` comment immediately after creating it; Issue publication alone is not a native trigger.
- A planning/deferred parent may coordinate repository-specific implementation Issues; without an explicit `@codex` instruction it never authorizes a task itself.
- Codex Cloud may edit only the repository it was started in. It receives no portfolio-wide publishing token and no persistent/shared/production infrastructure credential.
- Pull-request CI is deterministic and credential-free. Persistent infrastructure execution and deployment remain separate post-merge workflows with human approval and short-lived credentials where available.
- The portfolio GitHub Project is for status and visibility, not execution authority.

## Code Review Rules

- Report only consequential P0/P1 defects: security or authentication failures, data loss or corruption, broken persistence, incompatible integration contracts, unsafe permissions or secret exposure, broken rollback or deployment assumptions, serious user-visible regressions, or missing tests that leave serious behavior unverified.
- Do not report style, naming, minor maintainability, speculative P2/P3 improvements, or objections to settled product decisions.
- Code review is a quality gate only. It never authorizes merge, deployment, Terraform plan/apply, or any persistent real-world change.

## Commands

- Run `./tests/run.sh` after any workflow, template, installer, or policy change.
- Run `git diff --check` before handoff.

## Done

Keep changes minimal, update documentation with behavior, and complete the pull request's Merge Brief.
