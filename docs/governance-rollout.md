# Governance rollout

`governance/repositories.json` lists the managed repositories and the shared
Project fields they use. Update this small inventory when a repository or field
changes; never silently omit a client.

Before rollout, inspect each repository with `gh repo view`, confirm the client
templates and thin workflow callers are present, and check Project fields with
`gh project field-list`. Access or GitHub-plan failures require human review;
they are not proof of compliance or drift.

Current private repositories cannot enable branch protection on the present
GitHub plan. Keep reviewed PRs, hosted checks, canaries, and kill switches as
compensating controls. D’emand PR #55 remains the existing template canary and
its listed legacy branch expires when that PR closes.
