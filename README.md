# Development platform

`dev-platform` is the reviewed source for the portfolio's shared Codex policy, deterministic pull-request checks, governance conventions, and repository templates. Codex Cloud performs implementation and branch publication; this repository does not contain a custom agent runner or publisher.

## Architecture at a glance

| Part | Responsibility |
| --- | --- |
| Portfolio GitHub Project | Shows priority and status across repositories; native rules and the central reconciler keep open items present, but Project membership does not authorize execution. |
| Repository Implementation Issue | Records reviewed work that the coordinator queues by default. |
| Top-level `@codex` Issue comment | The owner's exact native trigger; the coordinator posts it immediately after creating ready work. |
| Codex Cloud | Implements that Issue on one issue-specific branch in its repository. |
| Coordinator | Publishes or updates the draft PR, verifies its SHA and CI, invokes independent review, and hands it to the owner. |
| `dev-platform` | Supplies shared policy, reusable CI, governance, Portfolio reconciliation, and starter templates. |
| Application repositories | Hold product code, product context, and repository-specific commands and rules. |
| Infrastructure repository | Holds infrastructure-as-code that Codex may edit and validate without persistent credentials. |
| Trusted post-merge workflows | Perform deployments and persistent infrastructure changes after human approval. |

## Lean operating model

1. Draft and review the work. Use **Implementation issue** for ready work and **Planning / deferred issue** as the explicit non-executable opt-out.
2. When the coordinator creates an Implementation Issue, it immediately posts the owner's exact supported top-level Codex comment. Publication alone is not a native trigger.
3. Codex runs one repository-scoped task on one issue-specific branch. Independent or non-overlapping Issues may run in parallel; serialize dependent or overlapping work through merged, green `main`.
4. When Cloud finishes, the coordinator uses native **Create PR/Update PR**, confirms the PR is draft, completes its Merge Brief, and verifies the published head SHA.
5. Deterministic CI runs without deployment credentials. The coordinator then requests one separate native `@codex review` limited to consequential P0/P1 findings.
6. Address consequential findings on the same branch, rerun affected CI, and perform at most one fresh review. Unresolved findings go to the owner.
7. Mark the PR ready and hand it to the owner only after publication, CI, and agent review. The owner explicitly reviews and merges.
8. Separate trusted post-merge workflows perform deployments or persistent infrastructure changes with their own authorization.

The owner's exact top-level `@codex implement this issue...` comment remains the queue action. The coordinator posts it by default for Implementation Issues without seeking a second approval; if it cannot act as the repository owner, that one comment remains the owner's manual step and the Issue stays `Todo`. An Issue-body mention is unsupported. Native Codex review is a bounded quality pass, not a custom AI-review Action, merge approval, or deployment authority. There is no custom dispatcher, publisher, convergence controller, or auto-merge system.

The D'EMAND canary proved the exact top-level owner-comment path; see [Cloud setup](docs/cloud-setup.md). Run the disposable canary when onboarding another repository or Codex Cloud environment; Issue-body mentions remain unsupported.

Use [Issue planning](docs/issue-planning.md) for unit sizing, concurrency, dependencies, and cross-repository integration contracts. See [Governance rollout](docs/governance-rollout.md) for the bounded review and Project lifecycle.

## Centralized pieces

- `policy/AGENTS.md`: portfolio-wide Codex defaults.
- `.github/workflows/ci.yml`: reusable credential-free CI and protected-path enforcement.
- `.github/workflows/governance.yml`: optional deterministic naming checks.
- `.github/workflows/portfolio-project.yml`: centralized open-item and lifecycle Status reconciliation.
- `templates/client/`: thin repository callers, Issue forms, Merge Brief, and local guidance skeletons.
- `client-setup`: conservative installer and readiness checker for new repositories.

Client workflow callers reference `atkandi111/dev-platform@main`, so reviewed platform workflow updates propagate automatically. Repository-local `AGENTS.md` files remain necessary for native GitHub review and repository-specific commands. In Codex Cloud, install the shared policy as global guidance so changes on `main` are fetched before each task; see [Cloud setup](docs/cloud-setup.md).

## Trust boundaries

- Codex Cloud authentication and repository access replace the former Actions-hosted OpenAI key and custom publisher token path.
- A task is repository-scoped. It cannot discover or escalate authority into another repository.
- Pull-request verification receives `contents: read` and no cloud/deployment credentials.
- Workflow and local action paths are protected by default because pull-request code must not redefine its own verifier.
- Application repositories do not receive infrastructure provisioning authority.
- The infrastructure repository may validate Terraform in pull-request CI, but persistent plan/apply remains a separate trusted workflow on `main` with explicit human approval.
- The GitHub Project remains the portfolio view; Project status is not an execution signal.

## Adoption

For a new repository:

```bash
./client-setup install /path/to/repository atkandi111/dev-platform
./client-setup check /path/to/repository
```

The installer refuses to overwrite existing files. Existing repositories should merge the templates deliberately. Configure the Codex Cloud environment separately using [docs/cloud-setup.md](docs/cloud-setup.md), then run the canary described there before relying on the owner-comment trigger in that environment.

For merge order, existing work, existing Issues, cleanup, and rollback, follow [docs/transition.md](docs/transition.md).
