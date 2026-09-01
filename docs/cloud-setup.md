# Codex Cloud setup

Use one Codex Cloud environment per repository. Grant access only to that repository and do not add deployment, persistent infrastructure, or portfolio-wide GitHub credentials.

## Shared guidance

Add a read-only GitHub token as the setup-only secret `DEV_PLATFORM_READ_TOKEN`. It needs access only to `atkandi111/dev-platform`. Configure this setup script:

```bash
set -euo pipefail
mkdir -p "$HOME/.codex"
curl --fail --silent --show-error --location \
  --header "Authorization: Bearer $DEV_PLATFORM_READ_TOKEN" \
  --header "Accept: application/vnd.github.raw+json" \
  https://api.github.com/repos/atkandi111/dev-platform/contents/policy/AGENTS.md?ref=main \
  --output "$HOME/.codex/AGENTS.md"
```

Use the same command as the maintenance script so every new task begins with the reviewed policy on `main`. Codex Cloud exposes setup secrets only during setup; do not copy the token into the repository or agent environment.

Repository-local `AGENTS.md` remains the source for repository commands and product-specific constraints. Codex layers it over the global policy.

## Required canary

Before enabling this as the normal queue path, publish one disposable implementation Issue in a low-risk repository and verify:

- publishing the Issue body alone does not start a task;
- the exact top-level `@codex implement this issue...` comment starts exactly one task;
- the task reads both the global and repository-local guidance;
- it changes only the authorized repository;
- after the task completes, **Create PR** publishes one pull request;
- the operator confirms or converts that pull request to draft and completes the repository Merge Brief;
- CI runs without secrets and protected workflow paths are rejected;
- closing/canceling the test leaves no deployed or persistent resource.

The first D'EMAND canary confirmed this sequence: the initial Issue-body mention did not start a task, while the later top-level comment did. The task completed, **Create PR** published the branch, and the operator converted the pull request to draft before review. See [issue #60](https://github.com/atkandi111/demandph-website/issues/60) and [PR #61](https://github.com/atkandi111/demandph-website/pull/61). Do not rebuild the former dispatcher.
