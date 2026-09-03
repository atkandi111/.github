# Transition to automatic Issue-to-PR publication

The prior flow used native Codex Cloud implementation followed by a manual **Create PR** handoff. The new flow uses an Actions-hosted Codex job plus a clean non-AI publisher so completed work reliably reaches one ready PR.

## Preserve existing work

- Continue existing product branches and PRs normally. Do not regenerate, rebase, or close them for this transition.
- The pipeline reacts only to owner-created Implementation Issues opened after its caller is enabled. It does not bulk-process existing Issues or PRs.
- Existing unpublished native Cloud work remains separate recovery work; the pipeline does not guess or recreate it.
- Keep backlog and planning parents unchanged. To run an existing Issue, implement it manually or replace it with a newly reviewed Implementation Issue that links the original. Adding a label later does not authorize it.
- Do not also post native `@codex implement` comments after adopting this pipeline.

## New Issues

- Owner-created **Implementation issue**: queues from its initial `implementation` label.
- **Planning / deferred issue**: remains Todo and non-executable from its initial `planning` label.
- One executable Issue stays repository-scoped and normally produces one PR. Cross-repository outcomes use a Planning parent and one Implementation subissue per repository.

## Rollout order

1. Merge the account `.github` implementation after tests and owner review.
2. Ensure the three required labels exist in every repository.
3. Create/install the narrowly scoped publisher App and add the App and OpenAI settings while `AGENT_PIPELINE_ENABLED=false`.
4. Merge each repository's thin caller PR separately without disturbing active product branches.
5. Optionally enable native Codex review.
6. Enable D'EMAND first and observe one real low-risk Implementation Issue, then enable remaining repositories individually.

Infrastructure may later permit credential-free Terraform checks. Persistent plan/apply remains outside this pipeline.

## Safe stop

Set `AGENT_PIPELINE_ENABLED=false`. Queued runs that reach authorization will no-op; already published PRs remain ordinary PRs for manual review and merge.
