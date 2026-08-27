# Change record naming

Issue titles describe the requested outcome: prefer 3-8 words, use sentence
case, stay within 60 characters, omit a trailing period, and keep repository,
status, priority, author, tool, task, and Conventional Commit prefixes out.
Status, Priority, and Waiting On belong in Project fields.

Human branches use `<type>/<short-kebab-scope>` with `feat`, `fix`, `docs`,
`refactor`, `test`, `ci`, or `chore`. Pipeline branches use `issue/<number>`.
Only registered automation prefixes such as `dependabot/` are allowed. New
`agent/` and `codex/` branches are rejected.

Pull-request titles and every proposed commit subject use Conventional Commit
format. Configure squash merging so the validated pull-request title becomes
the commit subject on `main`.

Exact legacy branch names may be temporarily registered in
`GOVERNANCE_LEGACY_BRANCHES`; wildcard legacy prefixes are not supported. Each
exception needs an owner and expiry in the repository inventory. Apply the
rules prospectively—do not rewrite history or rename inactive branches merely
for compliance.

The thin caller defaults `GOVERNANCE_NAMING_ENFORCED` to off. Enable it only
after the repository's agent pipeline uses `issue/<number>` and creates
Conventional Commit PR titles and subjects. Until then the check reports the
missing activation without rejecting active legacy automation.
