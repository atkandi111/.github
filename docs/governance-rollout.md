# Governance rollout

The portfolio GitHub Project remains the canonical view of status and priority. Repository workflows do not use Project fields as task authorization.

The reusable governance workflow validates only deterministic naming rules and is disabled by default through `GOVERNANCE_NAMING_ENFORCED`. Observe it before enabling. Cloud-generated branch names are accepted as automation and should not drive new parsing or classification logic.

Do not add semantic Issue classification, AI review, automated priority assignment, convergence loops, or auto-merge. Human-authored Issue contracts and Merge Briefs are the simpler control surface for a solo developer.
