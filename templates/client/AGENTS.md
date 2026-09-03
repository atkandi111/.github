# Repository instructions

Read the repository's product and planning documentation before implementation. The executable Issue defines the requested scope; do not invent missing product intent.

The portfolio-wide policy is loaded by the central implementation workflow. This file is the repository-specific overlay and must remain useful on its own for native GitHub review and local Codex work.

## Repository map

Document the important application directories here.

## Commands

- Build: document the command or `not applicable`.
- Test: document the command or `not applicable`.
- Lint: document the command or `not applicable`.
- Typecheck: document the command or `not applicable`.

## Repository-specific rules

Document only rules that differ from, or add necessary context to, the portfolio defaults.

## Code Review Rules

- Report only consequential P0/P1 defects: security or authentication failures, data loss or corruption, broken persistence, incompatible integration contracts, unsafe permissions or secret exposure, broken rollback or deployment assumptions, serious user-visible regressions, or missing tests that leave serious behavior unverified.
- Do not report style, naming, minor maintainability, speculative P2/P3 improvements, or objections to settled product decisions.
- Review is a quality gate only; it never authorizes merge, deployment, Terraform plan/apply, or persistent changes.

## Done

Keep changes within the Issue, update relevant documentation when durable behavior or workflow changes, add appropriate tests, and run applicable checks. If a meaningful user-visible or product decision is unspecified, stop and state the missing decision. The clean publisher, not the implementation task, owns branch and pull-request publication. Normal PR CI and optional native Codex review inform the owner; only the owner manually merges.
