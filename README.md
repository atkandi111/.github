# dev-platform

`dev-platform` is the centralized, deliberately small Internal Developer Platform for isolated client website repositories. V1 turns an explicitly authorized GitHub Issue into a reviewable Codex implementation; it does not own infrastructure or product decisions.

## V1 flow

```text
human Issue + agent label
→ trigger, actor, kill-switch, attempt, and concurrency guards
→ fresh Codex implementation run
→ isolated branch and draft PR
→ deterministic client commands and protected-path gate
→ optional client-owned preview
→ human merge, changes, or rejection
```

Codex stops with `HUMAN INPUT REQUIRED` when a meaningful product or user-visible decision is missing. There is no planner, AI reviewer, auto-merge, production deployment, or Terraform access.

## Connect a repository

1. Copy the contents of [`templates/client`](templates/client) into the client repository.
2. Pin both reusable workflow callers to a canary-tested `dev-platform` tag or commit; never track `main`.
3. Add the `agent` label and the variables/secrets listed in [`docs/operations.md`](docs/operations.md).
4. Ensure the repository exposes the applicable build, test, lint, and typecheck commands through repository variables.
5. Configure protected paths and, if supported, a separate limited-credential preview job.

Create an Issue with the agent task template, then have an authorized actor add `agent`. Remove the label before editing and re-add it to authorize another attempt.

## Stop the pipeline

- Repository: set `PIPELINE_ENABLED=false`.
- Organization: set `AGENT_PIPELINE_ENABLED=false` as an organization Actions variable.
- Emergency fallback: disable the client repository's **Agent implementation** workflow in GitHub Actions.

Existing runs can be cancelled from the Actions UI. Provider budget and usage alerts are a required operational control, not a custom service in this repository.

## Safety boundaries

The Codex job has repository read permission and the OpenAI credential is brokered by the official Action. A separate job, without the OpenAI secret, validates and publishes the patch. Protected paths fail before push and again in CI. Issue content is passed as action data, never embedded in executable shell. Production credentials and shared infrastructure are outside this pipeline.

See [`docs/architecture.md`](docs/architecture.md) for boundaries, [`docs/operations.md`](docs/operations.md) for setup and incidents, and [`docs/canary.md`](docs/canary.md) for rollout validation.

## Test a platform change

Run `./tests/run.sh`, review the diff, test all six scenarios in the non-client canary, tag the tested commit, and roll it to one or two clients before broader adoption.

