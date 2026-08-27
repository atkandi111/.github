# Vendor-official infrastructure skills

For GCP, AWS, or Terraform work, inspect the available skills before planning
or mutation. Use a matching vendor-official skill when one is registered in
`governance/official-skills.json` and available in the current environment.

A skill is vendor-official only when both are true:

- its publisher is controlled by Google Cloud, AWS, or HashiCorp; and
- its package ID, canonical source, exact version, and SHA-256 artifact digest
  match the approved registry entry and the skill loaded at runtime.

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

Add its stable name, immutable package ID and version, exact publisher,
canonical repository URL, SHA-256 artifact digest, evidence URL, verification
date, and bounded purpose to the correct vendor entry. Verification expires
after 365 days. Run `python3 scripts/check-skill-provenance.py` and obtain
review.

Before using an approved skill, export the environment's installed-skill
identity as a runtime manifest and require an exact match:

```sh
python3 scripts/check-skill-provenance.py \
  --runtime-manifest /path/to/runtime-skills.json \
  --require-skill approved-skill-name
```

The checker validates registry structure, fixed trust roots, canonical URLs,
verification freshness, and runtime identity. Reviewers must still verify that
the URLs exist, do not redirect outside the approved organization, and remain
under the vendor's control.
