# Decision 0001: explicitly dispatch CI

Status: accepted for V1

The publishing job creates its branch and draft PR with the repository `GITHUB_TOKEN`, then explicitly dispatches the tiny client `ci.yml` workflow on the new branch. GitHub documents that most events caused by `GITHUB_TOKEN` do not recursively start workflows, while `workflow_dispatch` always does. Current GitHub behavior can also leave automation-created PR events awaiting approval, which is not the reliable V1 path we need.

This requires narrowly scoped `actions: write` in the publishing job, avoids a PAT or GitHub App, and reliably starts deterministic CI. The dispatched run uses the branch SHA and therefore attaches checks to the proposed commit. Client CI also listens to normal `pull_request` events for human-created PRs.

Alternatives rejected for V1:

- GitHub App installation token: useful at larger scale, but adds an application and key lifecycle without a demonstrated need.
- Trusting PR/push recursion: not reliable with `GITHUB_TOKEN` event suppression/approval behavior.
- Running all CI inside the agent workflow: couples lifecycles and loses the reusable, independently rerunnable CI boundary.

References: [GitHub workflow triggering](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow) and [reusable workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows).

