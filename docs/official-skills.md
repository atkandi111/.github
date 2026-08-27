# Vendor-official infrastructure skills

For GCP, AWS, or Terraform work, inspect the available skills before planning
or mutation. Use a matching vendor-official skill when one is registered in
`governance/official-skills.json` and available in the current environment.

A skill is vendor-official only when both are true:

- its publisher is controlled by Google Cloud, AWS, or HashiCorp; and
- its canonical source is hosted by that vendor or its verified GitHub
  organization.

A similar name, internal recommendation, marketplace badge, or third-party
repository is not enough. Never describe an unregistered or unverified skill
as vendor-official.

The registry currently approves no vendor skills. This is intentional: if no
verified official skill is available, continue normally using repository
instructions and current authoritative documentation. Missing an official
skill is not a blocker and does not justify installing an unverified one.

Skills provide guidance, not authority. They never bypass repository approval,
plan review, deletion, IAM, ownership, rollback, secret-handling, Terraform
apply, deployment, or production-mutation gates.

## Register a skill

Add its stable name, exact publisher, canonical source URL, evidence URL,
verification date, and bounded purpose to the correct vendor entry. Run
`python3 scripts/check-skill-provenance.py` and obtain review. Reverify the
publisher and source before relying on an entry whose provenance changed.
