# Development platform

`dev-platform` is the reviewed source for the portfolio's shared Codex policy, deterministic pull-request checks, governance conventions, and repository templates. Codex Cloud performs implementation and branch publication; this repository does not contain a custom agent runner or publisher.

## Lean operating model

1. Draft and review work before publishing it.
2. Normally publish an **Implementation issue** in the repository that will change. Its `@codex` instruction starts one repository-scoped task and normally produces one draft pull request.
3. Use **Planning / deferred issue** only when publication must not start Codex. A coordination-only parent can link separately authorized Implementation subissues in each affected repository.
4. Codex implements in its authorized repository and completes the pull request's human-readable **Merge Brief**.
5. Central reusable CI and optional naming governance verify the pull request without deployment credentials.
6. A human reviews and merges. Separate trusted post-merge workflows perform deployments or persistent infrastructure changes.

Publishing the implementation Issue is the queue action. There is no second approval label, custom dispatcher, publisher, semantic classifier, AI reviewer, convergence controller, or auto-merge system.

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
