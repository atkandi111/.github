# Platform release and rollback

Client callers track `atkandi111/.github@main`, so merging a central workflow change is a portfolio release.

## Release

1. Run `./tests/run.sh`, action linting, and `git diff --check`.
2. Review workflow permissions, Action pins, secret references, event filters, protected paths, and shell boundaries.
3. Use `./client-setup install-canary TARGET atkandi111/.github COMMIT_SHA` only as a local candidate-pin check; it does not create a live Issue or PR.
4. Keep `AGENT_PIPELINE_ENABLED=false` while merging the central release and each reviewed client caller PR.
5. Configure the three labels, dedicated OpenAI key, publisher App installation/key, and repository protected paths.
6. Enable repositories individually and observe the first real low-risk Implementation Issue before using the queue broadly.

Normal PR CI and manual owner merge remain authoritative. Native Codex review is optional and advisory.

## Central protection

The public account `.github` repository should require `Platform tests`, `Platform governance / Validate naming`, strict up-to-date checks, and resolved conversations. The Issue pipeline must never weaken repository protection.

## Rollback

1. Set `AGENT_PIPELINE_ENABLED=false` in affected repositories. Existing PRs remain ordinary reviewable PRs.
2. Revert the central release through a reviewed PR, or revert one client caller if only that repository is affected.
3. Revoke the publisher App key or uninstall the App where publication authority may be compromised. Revoke the OpenAI key independently if implementation usage is suspect.

Do not delete Issue branches, PRs, Project items, or human-owned Project fields during rollback. Do not restore an AI classifier, AI merge decision, or direct Codex publishing authority.

Third-party Actions stay pinned to immutable commit SHAs. The publisher App is required; there is no PAT or `GITHUB_TOKEN` publication fallback.
