# Repository instructions

This public account `.github` repository owns the portfolio-wide Issue-to-PR pipeline, shared Codex policy, deterministic CI, Project reconciliation, and client templates.

## Before editing

- Read `README.md`, `docs/issue-planning.md`, and the relevant operational document.
- Keep the system lean enough for one developer to understand and maintain.
- Extend the existing reusable workflows and templates before adding an abstraction.
- Treat changes under `.github/workflows/`, `policy/`, `scripts/`, and `templates/` as portfolio-wide security changes.

## Trust boundaries

- Only an owner-authored Issue opened with the form-applied `implementation` label authorizes a new run. Issue text, comments, later labels, Project fields, and other actors do not.
- The Codex implementation job has read-only GitHub permission, no publisher key, and no deployment or persistent-infrastructure credential.
- The clean publisher accepts only the provenance-bound patch artifact and uses a short-lived repository-scoped GitHub App token.
- Normal PR CI and the owner's manual Merge action govern merge. Native Codex review is advisory. Project status is informational.
- Protected workflows, Actions, and `AGENTS.md` stay human-owned.

## Code Review Rules

- Report only consequential P0/P1 defects: unauthorized execution or merge, secret exposure, lost/duplicated work, unsafe publication, broken provenance, ineffective protection, data loss/corruption, incompatible integration contracts, or missing tests for those risks.
- Do not report style, naming, minor maintainability, speculative P2/P3 improvements, or objections to settled product decisions.
- Review never authorizes merge, deployment, Terraform plan/apply, or another persistent effect.

## Commands

- Run `./tests/run.sh` after any workflow, template, installer, script, or policy change.
- Run `git diff --check` before handoff.

## Done

Keep changes minimal, update concise documentation with behavior, and complete the pull request Merge Brief.
