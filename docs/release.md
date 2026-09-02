# Platform release and rollback

Client callers track `atkandi111/.github@main`. A merge to `main` is therefore a portfolio pipeline release.

## Release checks

1. Run `./tests/run.sh` and `git diff --check`.
2. Review every workflow permission, Action pin, secret reference, event filter, protected path, and shell boundary.
3. Use `./client-setup install-canary TARGET atkandi111/.github COMMIT_SHA` in a disposable directory to verify that agent, approval, CI, and governance callers all pin the candidate and that `platform_ref` matches it.
4. Keep `AGENT_PIPELINE_ENABLED=false` and `AGENT_AUTO_MERGE_ENABLED=false` in every repository while merging the central release and client caller PRs.
5. Merge the central PR only after owner review. Confirm `main` platform tests pass.
6. Roll out each client through its own reviewed Issue/PR so repository-specific CI and protected paths remain explicit.
7. Configure labels and credentials, enable native Codex automatic review, then observe the first real low-risk Implementation Issue before using the queue broadly.
8. Enable auto-merge only after the default branch satisfies every check in `docs/cloud-setup.md`. Private repositories without enforceable protection remain manual-merge.

No disposable revision-review canary is required. Codex review is advisory; deterministic CI and owner approval of the current revision remain the safety gates.

## Central repository protection

The public account `.github` repository should require:

- `Platform tests`;
- `Platform governance / Validate naming`;
- `atkandi/owner-approval` once its approval caller is on `main`;
- at least one approval with stale approvals dismissed;
- strict up-to-date checks; and
- resolved conversations.

Enable repository auto-merge only after those settings exist. The Issue pipeline itself must never weaken them.

## Rollback

1. Set `AGENT_PIPELINE_ENABLED=false` in affected repositories. Existing PRs remain ordinary reviewable PRs.
2. Set `AGENT_AUTO_MERGE_ENABLED=false` if the merge gate is suspect.
3. Revert the central release on `main` through a reviewed PR. Client callers then use the restored central behavior on their next event.
4. Revert a client caller separately if only that repository is affected.
5. Revoke the publisher App private key or uninstall the App from a repository if publication authority may be compromised. Revoke the dedicated OpenAI key independently if implementation usage is suspect.

Do not delete Issue branches, PRs, Project items, or human-owned Project fields as part of rollback. Do not restore the former AI classifier/reviewer or direct auto-merge prototype.

## Dependency policy

Pin third-party Actions to reviewed immutable commit SHAs. The central reusable workflow and thin client callers intentionally use `atkandi111/.github@main` as the reviewed release channel. The publisher App is required; there is no PAT or `GITHUB_TOKEN` fallback.
