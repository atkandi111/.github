# Platform release and rollback

Client callers track `atkandi111/.github@main`. A merge to `main` is therefore a portfolio workflow release; review and test it accordingly.

## Release checks

1. Run `./tests/run.sh`.
2. Use `./client-setup install-canary TARGET OWNER/REPOSITORY COMMIT_SHA` in a disposable directory or low-risk repository to verify exact candidate references.
3. For behavior that depends on Codex Cloud, account-default templates, native Create PR/Update PR, or GitHub comments, run the canaries in `docs/cloud-setup.md`.
4. On the published draft PR, verify its full head SHA, run deterministic CI, and request the separate native `@codex review` pass.
5. Merge the platform pull request only after the candidate checks pass and no consequential P0/P1 finding remains.
6. Confirm one client pull request uses the new `main` workflow successfully.

## Rollback

Revert the platform commit on `main` to restore the prior reviewed workflow and account-default template source. Existing client callers use the restored reusable workflow and inherited templates on their next run or new record. A repository with an intentional local template remains responsible for that override.

If Codex Cloud behavior is unreliable, stop posting the exact owner trigger comment while continuing to publish and refine implementation contracts or develop manually. There is no repository secret, custom queue service, or publisher to disable.

## Dependency policy

Pin third-party Actions to reviewed immutable commit SHAs. Reusable client callers intentionally use `atkandi111/.github@main` as the reviewed portfolio release channel.
