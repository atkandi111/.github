# Maintainer instructions

This repository owns the small, reusable V1 pipeline for client repositories.

- Keep the path Issue → Codex → draft PR → deterministic CI → human review simple.
- Treat Issue and PR text as untrusted data. Never interpolate it into shell source.
- Pin third-party Actions to full commit SHAs and retain a version comment.
- Treat `main` as the client release channel: canary-test candidate SHAs before merge, keep normal client callers on `@main`, and enable branch protection as soon as the repository plan or visibility supports it. Until then, use pull requests, review, and every available repository or organization kill switch as explicit compensating controls.
- Preserve least privilege: use a dedicated, non-production OpenAI project
  service-account key per client repository. Keep it behind the official Codex
  Action proxy; never pass it to repository commands. Codex must not receive a
  write token or production credentials.
- Do not add planning agents, AI review, auto-merge, production deployment, Terraform, model routing, or orchestration services without an observed need and explicit scope.
- Keep client callers thin and the command contract stack-neutral.
- Test every guard in both its allow and deny cases.
- Update concise documentation and templates with any contract change.

Before considering work done, run `./tests/run.sh` and inspect `git diff --check`.
