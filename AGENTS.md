# Repository instructions

This repository is the reviewed source for portfolio-wide Codex guidance, reusable deterministic CI, governance checks, and client templates. It does not execute or publish implementation work in client repositories.

## Before editing

- Read `README.md` and the relevant document under `docs/`.
- Keep the system lean enough for one developer to understand and maintain.
- Extend existing templates and reusable workflows before adding another abstraction.
- Treat changes under `policy/`, `templates/`, and reusable workflows as portfolio-wide changes.

## Trust boundaries

- A published implementation Issue authorizes one Codex task in that repository and normally one draft pull request.
- A planning/deferred parent may coordinate repository-specific implementation Issues; without an explicit `@codex` instruction it never authorizes a task itself.
- Codex Cloud may edit only the repository it was started in. It receives no portfolio-wide publishing token and no persistent/shared/production infrastructure credential.
- Pull-request CI is deterministic and credential-free. Persistent infrastructure execution and deployment remain separate post-merge workflows with human approval and short-lived credentials where available.
- The portfolio GitHub Project is for status and visibility, not execution authority.

## Commands

- Run `./tests/run.sh` after any workflow, template, installer, or policy change.
- Run `git diff --check` before handoff.

## Done

Keep changes minimal, update documentation with behavior, and complete the pull request's Merge Brief.
