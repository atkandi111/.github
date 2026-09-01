# Development platform

`dev-platform` is the reviewed source for the portfolio's shared Codex policy, deterministic pull-request checks, governance conventions, and repository templates. Codex Cloud performs implementation and branch publication; this repository does not contain a custom agent runner or publisher.

## Architecture at a glance

| Part | Responsibility |
| --- | --- |
| Portfolio GitHub Project | Shows priority and status across repositories; native rules and the central reconciler keep open items present, but Project membership does not authorize execution. |
| Repository Implementation Issue | Records the reviewed, repository-scoped implementation contract. |
| Top-level `@codex` Issue comment | Queues one Codex Cloud task after the contract is published. |
| Codex Cloud | Implements that Issue in its repository and prepares one pull request. |
| `dev-platform` | Supplies shared policy, reusable CI, governance, Portfolio reconciliation, and starter templates. |
| Application repositories | Hold product code, product context, and repository-specific commands and rules. |
| Infrastructure repository | Holds infrastructure-as-code that Codex may edit and validate without persistent credentials. |
| Trusted post-merge workflows | Perform deployments and persistent infrastructure changes after human approval. |

## Lean operating model

1. Draft and review work before publishing it.
2. Normally publish an **Implementation issue** in the repository that will change. Publication records the reviewed contract but does not start Codex.
3. Post the exact top-level `@codex implement this issue...` comment shown by the form to start one repository-scoped task.
4. When the task finishes, use **Create PR**, confirm or convert the pull request to draft, and ensure its human-readable **Merge Brief** is complete.
5. Use **Planning / deferred issue** for coordination that must not start Codex. A coordination-only parent can link separately authorized Implementation subissues in each affected repository.
6. Central reusable CI and optional naming governance verify the pull request without deployment credentials.
7. A human reviews and merges. Separate trusted post-merge workflows perform deployments or persistent infrastructure changes.

The explicit top-level Issue comment is the queue action. There is no approval label, custom dispatcher, publisher, semantic classifier, AI reviewer, convergence controller, or auto-merge system.

The D'EMAND canary proved the explicit-comment entry path; see [Cloud setup](docs/cloud-setup.md). Each additional repository still needs its own environment check before relying on the path there.

## Centralized pieces

- `policy/AGENTS.md`: portfolio-wide Codex defaults.
- `.github/workflows/ci.yml`: reusable credential-free CI and protected-path enforcement.
- `.github/workflows/governance.yml`: optional deterministic naming checks.
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

The installer refuses to overwrite existing files. Existing repositories should merge the templates deliberately. Configure the Codex Cloud environment separately using [docs/cloud-setup.md](docs/cloud-setup.md), then run the canary described there before relying on Issue mentions.

For merge order, existing work, existing Issues, cleanup, and rollback, follow [docs/transition.md](docs/transition.md).
