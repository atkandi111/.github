# Issue pipeline setup

GitHub Actions runs `openai/codex-action` with a dedicated API key to produce an isolated patch. A separate non-AI publisher validates and publishes it. Native Codex review is optional and uses the repository's Codex connection.

Do not also use an Issue-level `@codex implement` trigger; it would start a separate native Cloud task.

## 1. Create the publisher GitHub App once

Create a private GitHub App owned by `atkandi111` with repository permissions:

- **Contents: Read and write**;
- **Issues: Read and write**;
- **Pull requests: Read and write**; and
- Metadata read.

Grant no Administration, Actions, Workflows, Deployments, Environments, Secrets, organization, Project, or cloud permission. Install it only on repositories using the pipeline. Generate a private key and record the App Client ID. Never put the key in commands, Issues, PRs, logs, or Codex environments.

## 2. Configure each repository while disabled

```bash
./client-setup labels OWNER/REPOSITORY
```

Add these repository Actions settings:

| Kind | Name | Value |
| --- | --- | --- |
| Secret | `OPENAI_API_KEY` | Dedicated non-production OpenAI project key. |
| Secret | `PUBLISHER_APP_PRIVATE_KEY` | Publisher App private key. |
| Variable | `PUBLISHER_APP_CLIENT_ID` | Publisher App Client ID. |
| Variable | `AGENT_PIPELINE_ENABLED` | `false` during setup. |
| Variable | `AGENT_PROTECTED_PATHS` | Additional newline-separated repository-specific protected globs. |

The Codex and publisher credentials exist in the same repository but never enter the same job. Missing configuration fails closed.

Application repositories should protect infrastructure, deployment, migration, and other authority-bearing paths. Infrastructure repositories may permit IaC edits that credential-free PR CI can validate, but never expose plan/apply credentials to this pipeline.

## 3. Install the thin callers

```bash
./client-setup onboard /path/to/repository atkandi111/.github OWNER/REPOSITORY
./client-setup check /path/to/repository
```

Tailor the separate CI caller, merge its PR manually while the pipeline is disabled, and then set `AGENT_PIPELINE_ENABLED=true`.

## 4. Optional native review

Connect the repository and enable automatic review in [Codex Code Review settings](https://chatgpt.com/codex/settings/code-review). Review remains advisory and is not read or enforced by the pipeline.

## First real Issue

Use the first real low-risk Implementation Issue as the observation pass. Confirm one workflow run, one `issue/<number>` branch, one ready PR, the exact published SHA in its Merge Brief, and normal PR CI without a manual Create PR step.

If a run fails, correct the configuration and dispatch the Issue number through the workflow's owner-only retry. Keep the same Issue and PR.

## Normal operation

- Implementation Issue creation queues work.
- Planning / deferred creation does not.
- An exact-current-SHA owner changes-requested review queues a revision on the same PR.
- The owner manually merges when satisfied.
