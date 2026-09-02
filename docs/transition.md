# Transition to automatic Issue-to-PR publication

The portfolio previously used native Codex Cloud implementation followed by a manual **Create PR** handoff. The transition replaces that middle handoff with a small Actions-hosted implementation and clean publisher. Existing product work is preserved.

## Existing branches and pull requests

- Continue existing product branches and PRs normally. Do not regenerate, rebase, or close them merely for this transition.
- The new pipeline reacts only to owner-created Implementation Issues opened after its caller is enabled. It does not bulk-process existing PRs.
- Existing native Cloud commits that were never published remain separate recovery work; the pipeline does not guess or recreate them.

## Existing Issues

- Existing open Issues are not automatically authorized because their original `opened` event did not carry the new trusted receipt path.
- Keep backlog and planning parents unchanged.
- When an existing Issue is ready, either implement it manually or replace it with a newly reviewed Implementation Issue that links the original. Do not authorize it by adding `implementation` later.
- Do not post native `@codex implement` comments after adopting this pipeline; doing so could start duplicate work.

## New Issues

- Owner-created **Implementation issue**: queues automatically from its initial `implementation` label.
- **Planning / deferred issue**: remains Todo and non-executable from its initial `planning` label.
- One executable Issue stays repository-scoped and normally produces one PR. Cross-repository outcomes use one Planning parent and one Implementation subissue per repository.

## Rollout order

1. Merge the account `.github` implementation after its tests and owner review.
2. Create the four required labels in every in-scope repository.
3. Create/install the narrowly scoped publisher GitHub App and add the repository-local App Client ID/private-key settings.
4. Add a dedicated non-production OpenAI project key to each repository.
5. Keep both pipeline variables false while each client merges its thin agent and owner-approval callers.
6. Enable automatic native Codex review in each connected repository.
7. Protect `main` and enable auto-merge only where GitHub can enforce the full gate. Keep private unsupported repositories manual-merge.
8. Enable the D'EMAND pipeline first and observe one real low-risk Implementation Issue. Then enable the remaining repositories one at a time.

The infrastructure repository may later permit credential-free Terraform format/validate/test in its caller. Persistent plan/apply remains outside this pipeline.

## Safe stop

Set `AGENT_PIPELINE_ENABLED=false` to stop new implementation. Queued runs that reach authorization will no-op. Published PRs stay intact for ordinary human review. Set `AGENT_AUTO_MERGE_ENABLED=false` to prevent future PRs from being armed. Native auto-merge is persistent GitHub state, so also disable auto-merge on every already-armed PR in the GitHub UI or with `gh pr merge PR_NUMBER --disable-auto --repo OWNER/REPOSITORY`.
