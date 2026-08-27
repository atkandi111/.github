# Governance rollout

`governance/repositories.json` is the reviewed inventory for current and future
repositories. Add, rename, transfer, archive, or remove a repository through a
focused pull request; never silently exempt it.

Run the read-only audit with:

```bash
python3 scripts/portfolio-audit.py --json
```

The audit checks repository access, default branches, every enabled merge
method, the exact required-check contexts and effective classic/ruleset controls
on `main`, canonical SHA-256 contracts for synchronized files, Project access,
and the unique identity, type, and options of required Project fields. Local
`AGENTS.md` and `PROJECT.md` files use explicit size-bounded overlay contracts
instead of centralized content replacement.

Required contexts are role-specific and must have a checked-in producer. The
platform emits `Platform tests` and `Platform governance / Validate governance
naming`; installed clients emit `dev-platform/deterministic-ci` and `Client
governance / Validate governance naming`.

Exit `0` means pass, `1` means confirmed remediable drift, and `2` means
`HUMAN INPUT REQUIRED`. Authentication, rate-limit, response-shape, and plan
failures are indeterminate—not missing resources. The audit never changes
repository or Project state.

Current private repositories cannot enable branch protection or rulesets on the
present GitHub plan. Retain reviewed PRs, CI, canaries, and kill switches as
compensating controls, but do not call them full enforcement.

D’emand PR #55 is the template canary. Update it in place after the canonical
templates are reviewed; do not open a duplicate. Its exact legacy branch
exception is queried on every audit and expires when that PR closes. Every
exception needs an owner and a machine-readable expiry; an unmanaged repository
also needs its own active exception and remains visible in the report. A legacy
branch exception is valid only while that exact branch remains the expiry PR's
head in the same repository.

The later mutation phase must remain idempotent, open focused rollout PRs,
preserve repository-local `AGENTS.md` content, use a separately approved
Project credential, and provide dry-run, rollback, emergency-disablement, and
credential-revocation paths before activation.
