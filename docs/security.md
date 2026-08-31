# Security and trust boundaries

## Authorization

The executable object is a published Implementation Issue in one repository. The owner's reviewed Issue text and `@codex` instruction authorize one repository-scoped Codex Cloud task, normally producing one draft pull request. A Planning/deferred parent without that instruction and the portfolio GitHub Project provide coordination and visibility only.

Codex Cloud's GitHub installation, user authorization, repository selection, and platform controls replace the former custom authorized-actor/label/kill-switch/attempt/concurrency guard. Do not recreate those controls inside this repository unless a demonstrated Cloud limitation makes one strictly necessary.

## Credential separation

- The Codex task receives access only to its repository. It receives no Actions publishing token, portfolio-wide token, production credential, or persistent/shared infrastructure authority.
- Pull-request CI uses `contents: read` and no deployment secrets.
- Application repositories cannot provision infrastructure merely because Terraform exists elsewhere.
- The infrastructure repository may let Codex edit infrastructure-as-code and run local or credential-free format, validate, lint, and test checks.
- Credentialed Terraform plan/apply and application deployment execute only in separate trusted workflows after human review. Prefer OIDC and narrowly scoped short-lived roles; keep any unavoidable provider token out of Codex and pull-request jobs.

## Protected paths

The reusable CI workflow rejects changes to `.github/workflows/**` and `.github/actions/**` by default. Client callers may add repository-specific paths. It compares the immutable pull-request head with the trusted base using NUL-delimited, rename-disabled path output.

An intentional verifier change is a platform or manually supervised maintenance change, not an ordinary implementation Issue. Merge it through a controlled transition before requiring the updated check; do not add a label-based bypass to untrusted pull-request code.

The current private repositories do not have enforceable branch protection or rulesets under the present GitHub plan. CI and protected-path failures therefore provide visible, deterministic evidence but cannot technically prevent an authorized maintainer from merging. Treat a failed required check as a do-not-merge signal; human review remains the enforcement point until repository settings can make the checks mandatory.

## Fail-closed behavior

- Invalid or non-immutable head SHAs fail before checkout.
- A missing base reference fails the protected-path gate.
- Any configured check failure fails CI.
- Missing product intent must be surfaced for human direction rather than guessed.
- No workflow merges, deploys, applies Terraform, or broadens repository access on behalf of Codex.

The final human approval point is pull-request review and merge. Persistent effects happen only after that boundary.
