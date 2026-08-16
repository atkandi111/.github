# Maintainer instructions

This repository owns the small, reusable V1 pipeline for client repositories.

- Keep the path Issue → Codex → draft PR → deterministic CI → human review simple.
- Treat Issue and PR text as untrusted data. Never interpolate it into shell source.
- Pin third-party Actions to full commit SHAs and retain a version comment.
- Treat `main` as the integration branch and the moving `v1` tag as the client release channel: canary-test exact candidate SHAs, create an immutable `v1.x.y` release, and move `v1` only after review. Keep normal client callers on `@v1`, and enable branch protection as soon as the repository plan or visibility supports it. Until then, use pull requests, review, and every available repository or organization kill switch as explicit compensating controls.
- Preserve least privilege: use GitHub OIDC and short-lived OpenAI workload tokens; Codex must not receive a write token, long-lived API key, or production credentials.
- Do not add planning agents, AI review, auto-merge, production deployment, Terraform, model routing, or orchestration services without an observed need and explicit scope.
- Keep client callers thin and the command contract stack-neutral.
- Test every guard in both its allow and deny cases.
- Update concise documentation and templates with any contract change.

Before considering work done, run `./tests/run.sh` and inspect `git diff --check`.
