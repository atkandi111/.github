# Naming conventions

## Issues

Use a concise sentence-case title without a final period. Keep status, priority, and portfolio metadata in the GitHub Project.

## Branches and pull requests

Human-created branches use `<type>/<short-kebab-scope>`, where `<type>` is `feat`, `fix`, `docs`, `refactor`, `test`, `ci`, or `chore`. The Issue pipeline exclusively uses `issue/<number>` for its published branch. Branch naming supports idempotency but never creates authorization by itself.

Pull-request titles and human-authored commit subjects use Conventional Commit form, for example `feat(search): add result filters`. The publisher normalizes its PR title and commit subject deterministically; Codex does not commit directly.

The reusable governance workflow remains optional. Enable only deterministic rules that reduce real friction.
