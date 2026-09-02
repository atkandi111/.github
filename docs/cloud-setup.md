# Issue pipeline and Codex review setup

The implementation runner and reviewer are intentionally separate:

- GitHub Actions runs `openai/codex-action` with a dedicated API key to produce an isolated patch. It has no GitHub write authority.
- Native Codex Cloud Code Review reads the published PR after it becomes ready. It uses the repository's Codex connection and does not need the Actions API key.

Do not configure a native `@codex implement` Issue trigger. That is a separate Cloud execution path and would duplicate this pipeline.

## 1. Create the publisher GitHub App once

Create a private GitHub App owned by `atkandi111` with:

- Repository permissions: **Administration: Read**, **Contents: Read and write**, **Issues: Read and write**, **Pull requests: Read and write**, and Metadata read.
- No Actions, Workflows, Deployments, Environments, Secrets, organization, Project, or cloud permissions.
- Installation limited to the repositories using the pipeline.

Generate a private key and record the App's Client ID. The workflow requests a one-hour installation token and downscopes it again to the current repository and these exact permissions. Keep the long-lived private key only as a repository Actions secret; never put it in commands, Issues, PRs, logs, or Codex environments.

## 2. Configure each repository while disabled

Create the required labels:

```bash
./client-setup labels OWNER/REPOSITORY
```

Create these Actions settings in the repository:

| Kind | Name | Value |
| --- | --- | --- |
| Secret | `OPENAI_API_KEY` | Key from a dedicated non-production OpenAI project for this repository. |
| Secret | `PUBLISHER_APP_PRIVATE_KEY` | Publisher App private key. |
| Variable | `PUBLISHER_APP_CLIENT_ID` | Publisher App Client ID. |
| Variable | `AGENT_PIPELINE_ENABLED` | `false` during setup. |
| Variable | `AGENT_AUTO_MERGE_ENABLED` | `false` until protection is verified. |
| Variable | `AGENT_REQUIRED_CI_CONTEXT` | Exact required status context produced by this repository's deterministic CI caller. |
| Variable | `AGENT_MAX_ATTEMPTS` | `2`. |
| Variable | `AGENT_PROTECTED_PATHS` | Additional newline-separated repository-specific protected globs. |

For application repositories, protect infrastructure, Terraform, deployment-policy, and other authority-bearing paths. For the centralized infrastructure repository, allow only IaC edits that credential-free PR CI can validate; never pass plan/apply credentials to this pipeline.

The OpenAI key and publisher key are present in the same repository but never in the same job. The Codex job references only the OpenAI key. Clean publisher jobs reference only the App key.

## 3. Install and review the thin callers

```bash
./client-setup onboard /path/to/repository atkandi111/.github OWNER/REPOSITORY
./client-setup check /path/to/repository
```

Customize the copied CI commands and protected paths through repository variables. Merge the caller PR manually while the pipeline remains disabled. Client callers reference `atkandi111/.github@main`; future central workflow releases then apply automatically.

## 4. Enable native Codex review

In [Codex Code Review settings](https://chatgpt.com/codex/settings/code-review):

1. connect only the intended repository;
2. enable **Code review**; and
3. enable **Automatic reviews**.

Automatic review starts when the pipeline changes the initial draft PR to ready. Codex follows the repository's applicable `AGENTS.md` rules and reports P0/P1 findings. It is advisory: the owner decides whether findings are resolved. On a revision, a fresh review may be requested with `@codex review`, but it is not a merge requirement.

## 5. Configure merge protection where GitHub supports it

Before setting `AGENT_AUTO_MERGE_ENABLED=true`, the default branch must enforce:

- strict required deterministic CI whose exact status context matches `AGENT_REQUIRED_CI_CONTEXT`;
- required status `atkandi/owner-approval`;
- at least one approving review;
- dismissal of stale approvals after new commits; and
- resolved review conversations.

Also enable repository auto-merge. The pipeline rechecks these settings and the exact configured deterministic CI context before arming `gh pr merge --auto`. If any check is absent or the API cannot read protection, it leaves manual owner merge in place.

The current GitHub plan cannot enforce branch protection on private client repositories. Keep `AGENT_AUTO_MERGE_ENABLED=false` there until the repository becomes public or the account has the required GitHub plan. Do not emulate approval enforcement inside a merge-capable workflow.

## 6. Enable and observe the first real low-risk Issue

Set `AGENT_PIPELINE_ENABLED=true`, then create one reviewed low-risk Issue with the inherited **Implementation issue** form. Confirm:

- the Issue opens with `implementation` and receives `agent:authorized` plus `agent:in-progress`;
- exactly one workflow run starts and one `issue/<number>` branch/draft PR appears;
- the Merge Brief contains the published full SHA;
- deterministic CI runs without manual workflow approval;
- the PR becomes ready only after CI passes;
- automatic Codex review appears when enabled; and
- owner approval applies only to the current SHA.

This uses the first real low-risk change instead of requiring a disposable revision-review canary. If publication or CI fails, keep the same Issue and PR, correct the configuration, and use the workflow's manual `issue_number` dispatch. Do not create a second PR.

## Normal operation

- Implementation Issue creation is the queue action.
- Planning / deferred Issue creation is not executable.
- Owner changes-requested review queues one revision on the same PR.
- Owner approval is the merge authorization.
- Automatic merge is available only where native protection is enforceable; otherwise the final click remains manual.
