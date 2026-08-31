# Platform release and rollback

Client callers track `atkandi111/dev-platform@main`. A merge to `main` is therefore a portfolio workflow release; review and test it accordingly.

## Release checks

1. Run `./tests/run.sh`.
2. Use `./client-setup install-canary TARGET OWNER/REPOSITORY COMMIT_SHA` in a disposable directory or low-risk repository to verify exact candidate references.
3. For behavior that depends on Codex Cloud or GitHub Issue mentions, run the canary in `docs/cloud-setup.md`.
4. Merge the platform pull request only after the candidate checks pass.
5. Confirm one client pull request uses the new `main` workflow successfully.

## Rollback

Revert the platform commit on `main` to restore the prior reviewed workflow and template source. Existing client callers then use the restored reusable workflow on their next run. Repository-local template copies do not change automatically; revert or update those explicitly where adopted.

If Codex Cloud behavior is unreliable, stop publishing implementation Issues or omit the `@codex` instruction while continuing normal manual development. There is no repository secret, custom queue service, or publisher to disable.

## Dependency policy

Pin third-party Actions to reviewed immutable commit SHAs. Reusable client callers intentionally use `dev-platform@main` as the reviewed portfolio release channel.
