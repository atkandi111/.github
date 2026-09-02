# Codex Cloud setup

Use one Codex Cloud environment per repository. Grant access only to that repository and do not add deployment, persistent infrastructure, or portfolio-wide GitHub credentials.

## Shared guidance

The account policy is public and needs no setup token. Configure this setup script:

```bash
set -euo pipefail
mkdir -p "$HOME/.codex"
curl --fail --silent --show-error --location \
  https://raw.githubusercontent.com/atkandi111/.github/main/policy/AGENTS.md \
  --output "$HOME/.codex/AGENTS.md"
```

Use the same command as the maintenance script so every new task begins with the reviewed policy on `main`. Do not add a GitHub token merely to read this public file.

Repository-local `AGENTS.md` remains the source for repository commands and product-specific constraints. Codex layers it over the global policy.

## Required canary

Before enabling this as the normal queue path, publish one disposable Implementation Issue in a low-risk repository, then post the exact owner trigger comment and verify:

- publishing the Issue alone does not start Codex;
- the exact new top-level owner comment starts exactly one task;
- the task reads both the global and repository-local guidance;
- it changes only the authorized repository;
- after the task completes, **Create PR** publishes one pull request;
- the operator confirms or converts that pull request to draft and completes the repository Merge Brief;
- CI runs without secrets and protected workflow paths are rejected;
- closing/canceling the test leaves no deployed or persistent resource.

The first D'EMAND canary confirmed this sequence: the initial Issue-body mention did not start a task, while the later top-level comment did. The task completed, **Create PR** published the branch, and the operator converted the pull request to draft before review. See [issue #60](https://github.com/atkandi111/demandph-website/issues/60) and [PR #61](https://github.com/atkandi111/demandph-website/pull/61).

Issue-body mentions, quoted or edited text, and comments from other actors are unsupported. Keep the exact top-level owner comment as the single queue action; do not rebuild the former dispatcher.

The coordinator posts that comment automatically only when it is authenticated as the repository owner. Otherwise the owner must post it manually; the Issue remains `Todo` and no task starts until that happens.

## Native pull-request publication

Codex Cloud may prepare a branch without publishing a pull request automatically. The coordinator owns the native **Create PR/Update PR** action after the task finishes, then must:

1. confirm or convert the pull request to draft;
2. complete its Merge Brief;
3. verify that GitHub's full head SHA matches the published task output; and
4. keep the task counted as active until those checks pass.

Do not provide a reusable GitHub PAT or add a custom publisher. Native repository access is enough; force pushes, direct pushes to `main`, merge, deployment, and production mutation remain outside the task.

## Native Code Review

In [Codex Code Review settings](https://chatgpt.com/codex/settings/code-review), enable **Code review** for each repository after its Cloud environment exists. Automatic reviews are unnecessary: after deterministic CI passes on the real draft PR, the coordinator posts exactly `@codex review` so the review is explicitly sequenced and separate from implementation. GitHub Code Review reports P0/P1 findings and follows applicable `AGENTS.md` rules.

Canary the exact draft-PR behavior once per repository. A passing canary requires the 👀 reaction followed by a posted GitHub review. If draft review is unsupported, make the PR ready, request the review immediately, and return it to draft if consequential fixes are needed. Record the exact behavior; do not claim success from the comment alone.
