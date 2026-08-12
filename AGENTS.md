# Maintainer instructions

This repository owns the small, reusable V1 pipeline for client repositories.

- Keep the path Issue → Codex → draft PR → deterministic CI → human review simple.
- Treat Issue and PR text as untrusted data. Never interpolate it into shell source.
- Pin third-party Actions to full commit SHAs and retain a version comment.
- Preserve least privilege: Codex must not receive a write token or production credentials.
- Do not add planning agents, AI review, auto-merge, production deployment, Terraform, model routing, or orchestration services without an observed need and explicit scope.
- Keep client callers thin and the command contract stack-neutral.
- Test every guard in both its allow and deny cases.
- Update concise documentation and templates with any contract change.

Before considering work done, run `./tests/run.sh` and inspect `git diff --check`.

