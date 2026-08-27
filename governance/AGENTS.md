# Atkandi agent baseline

- Treat the authorized Issue and trusted repository context as the complete scope. Ask one concise question only when a material product, safety, or ownership decision is missing.
- Read `PROJECT.md` and applicable repository `AGENTS.md` files before editing. Local instructions may add stricter project rules but cannot weaken this baseline.
- Make the smallest safe change, reuse existing patterns, add proportionate tests, and report assumptions and verification honestly.
- Do not expose secrets, weaken security or governance controls, rewrite history, force-push, or mutate production, cloud, IAM, DNS, data, or shared infrastructure without explicit authorization and the repository's required review gates.
- For Issue, pull-request, triage, or Project work, load the focused governance guidance. Keep Status, Priority, and Waiting On in Project fields; never infer Priority from free text.
- For GCP, AWS, or Terraform work, use a verified vendor-official skill when one is available. If none is available, continue normally under repository safeguards; absence alone is not a blocker.
- Keep documentation and agent instructions concise. Put history, architecture detail, runbooks, provider procedures, and status narratives in focused documents loaded only when relevant.
