# Security and trust boundaries

## Authorization

The executable contract is a reviewed Implementation Issue in one repository. The coordinator queues it by default with the repository owner's exact new top-level trigger comment; publication alone does not start Codex. The trigger authorizes one repository-scoped Cloud task and issue-specific branch. The coordinator uses native **Create PR/Update PR**, confirms the PR is draft, completes the Merge Brief, and verifies its published SHA. A Planning/deferred parent and the portfolio GitHub Project provide coordination and visibility only.

Codex Cloud's GitHub installation, user authorization, repository selection, and platform controls replace the former custom authorized-actor/label/kill-switch/attempt/concurrency guard. Do not recreate those controls inside this repository unless a demonstrated Cloud limitation makes one strictly necessary.

## Credential separation

- The Codex task receives access only to its repository. It receives no Actions publishing token, portfolio-wide token, production credential, or persistent/shared infrastructure authority.
- Pull-request CI uses `contents: read` and no deployment secrets.
- Native Codex Code Review reads the published PR and applicable repository guidance as a quality gate. It does not receive or grant merge, deployment, Terraform plan/apply, or persistent-mutation authority.
- Application repositories cannot provision infrastructure merely because Terraform exists elsewhere.
- The infrastructure repository may let Codex edit infrastructure-as-code and run local or credential-free format, validate, lint, and test checks.
- Credentialed Terraform plan is generated only from reviewed `main` in a separately controlled workflow. Apply requires explicit human authorization of that exact saved plan, provenance, and checksum. Prefer OIDC and narrowly scoped short-lived roles; keep any unavoidable provider token out of Codex, review, and pull-request jobs. Code/merge approval and production-plan approval are separate human decisions.

## Protected paths

The reusable CI workflow rejects changes to `.github/workflows/**` and `.github/actions/**` by default. Client callers may add repository-specific paths. It compares the immutable pull-request head with the trusted base using NUL-delimited, rename-disabled path output.

An intentional verifier change is a platform or manually supervised maintenance change, not an ordinary implementation Issue. Merge it through a controlled transition before requiring the updated check; do not add a label-based bypass to untrusted pull-request code.

The current private repositories do not have enforceable branch protection or rulesets under the present GitHub plan. CI and protected-path failures therefore provide visible, deterministic evidence but cannot technically prevent an authorized maintainer from merging. Treat a failed required check as a do-not-merge signal; human review remains the enforcement point until repository settings can make the checks mandatory.

## Fail-closed behavior

Issue bodies and comments are untrusted data. Portfolio status mirroring compares comment fields as data and accepts only the exact unedited trigger from the repository owner; it never evaluates comment text as shell source. The `PORTFOLIO_PROJECT_TOKEN` remains confined to the central reconciliation job and can update membership and Status only through reviewed commands.

- Invalid or non-immutable head SHAs fail before checkout.
- A missing base reference fails the protected-path gate.
- Any configured check failure fails CI.
- Missing product intent must be surfaced for human direction rather than guessed.
- No workflow merges, deploys, applies Terraform, or broadens repository access on behalf of Codex.

Independent Codex review may identify P0/P1 defects but cannot approve merge or persistent effects. The final code approval point is human pull-request review and merge; production or shared-infrastructure execution has its own later human authorization.
