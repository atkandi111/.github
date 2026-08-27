# Governance rollout

`governance/repositories.json` is the reviewed inventory for current and future
repositories. Add, rename, transfer, archive, or remove a repository through a
focused pull request; never silently exempt it.

Run the read-only audit with:

```bash
python3 scripts/portfolio-audit.py --json
```

The audit checks repository access, default branches, merge settings, main
protection, required managed files, Project access, and Project field names.
Exit `0` means pass, `1` means remediable drift, and `2` means `HUMAN INPUT
REQUIRED`. It never changes repository or Project state.

Current private repositories cannot enable branch protection or rulesets on the
present GitHub plan. Retain reviewed PRs, CI, canaries, and kill switches as
compensating controls, but do not call them full enforcement.

D’emand PR #55 is the template canary. Update it in place after the canonical
templates are reviewed; do not open a duplicate. Its exact legacy branch
exception expires when that PR closes.

The later mutation phase must remain idempotent, open focused rollout PRs,
preserve repository-local `AGENTS.md` content, use a separately approved
Project credential, and provide dry-run, rollback, emergency-disablement, and
credential-revocation paths before activation.
