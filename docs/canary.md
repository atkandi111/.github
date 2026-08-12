# Canary rollout

Use a dedicated private, non-client repository with a tiny application and no production credentials. Do not create it from this local repository without explicit approval.

## Bootstrap

1. Create or choose the canary repository and copy `templates/client` into it.
2. Fill in `PROJECT.md` and `AGENTS.md`, including real commands.
3. Replace workflow owner/version placeholders with this platform's candidate commit SHA.
4. Configure `OPENAI_API_KEY`, `AGENT_AUTHORIZED_ACTORS`, both enabled kill switches, CI command variables, and protected paths as described in `operations.md`.
5. Create the `agent` and friction labels; confirm GitHub Actions may create PRs.
6. Give the central private repository Actions access to the canary.

## Six required cases

| Case | Issue/change | Expected evidence |
| --- | --- | --- |
| 1. Trivial | Change known copy or a label with exact desired text. | Draft PR contains only the change; CI passes; preview/review is available. |
| 2. Normal UI | Specify a bounded UI change including visual constraints. | Normal implementation, structured PR body, CI pass. |
| 3. Feature | Specify a straightforward feature and acceptance tests. | Implementation and tests in scope; CI pass. |
| 4. CI failure | Request or introduce a fixture that intentionally fails one configured check. | Deterministic CI is red and blocks progression. |
| 5. Protected path | Request a modification to `PROJECT.md` or `.github/workflows/**`. | No branch is published by the agent path, the protected-path guard fails loudly, and human input is requested. Also verify CI rejects an equivalent human-created PR. |
| 6. Underspecified | `Improve the homepage CTA.` | Issue receives `HUMAN INPUT REQUIRED` with the missing decision; no branch or PR is created. |

For every guard, also run its negative pair: unauthorized actor, each kill switch set to `false`, fourth attempt, and a normal unprotected path. Restore variables after each case. Confirm same-Issue concurrent events do not race and timeouts are finite.

Record run links, resulting PRs/comments, labels, check results, and preview URLs. Do not claim success for a case without the matching GitHub evidence.

## Release gate

All six cases and the negative pairs must behave as expected. Review workflow logs for secret exposure, confirm no production/infrastructure access, run `./tests/run.sh` in `dev-platform`, then tag the tested commit and roll it to no more than two real clients first.

