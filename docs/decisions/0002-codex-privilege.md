# Decision 0002: separate reasoning from publication

Status: accepted for V1

The official `openai/codex-action` runs in a job with `contents: read`, `workspace-write`, `drop-sudo`, an ephemeral session, and the OpenAI API secret. The job captures a binary Git patch and final message as an artifact. A clean, separate job downloads the artifact, has no OpenAI secret, validates protected paths, and alone receives repository/PR/Actions write permissions.

This materially limits credential overlap without a custom service. Fixed patch capture and artifact upload are the only steps after Codex in the reasoning job; no repository script executes there. The publishing job applies the patch as data and does not run agent-written application code.

The official Action's current documentation describes API-key proxying, `drop-sudo`, sandbox modes, `--ephemeral`, actor allowlists, and the need to constrain trigger/input handling. External Actions are pinned to full commit SHAs with version comments in workflow source.

Reference: [OpenAI Codex GitHub Action](https://learn.chatgpt.com/docs/github-action).

