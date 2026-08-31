# Naming conventions

## Issues

Use a concise sentence-case title without a final period. Keep status, priority, and portfolio metadata in the GitHub Project.

## Branches and pull requests

Human-created branches use `<type>/<short-kebab-scope>`, where `<type>` is `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, or `chore`. Codex Cloud may choose its own generated branch name; branch naming is not an authorization boundary.

Pull-request titles and human-authored commit subjects use Conventional Commit form, for example `feat(search): add result filters`. Do not require Codex-generated intermediate commits to conform when the platform controls them.

The reusable governance workflow remains optional. Enable only deterministic rules that reduce real friction; do not block useful work merely to normalize Cloud-generated branch names.
