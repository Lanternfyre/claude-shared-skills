# Stacked PRs

Use this only for `BEADWORK_DELIVERY=stack`. It requires the project's installed `gh stack` extension; do not install or replace the delivery tooling mid-task without need. Independent PRs and local integration are described in [delivery.md](delivery.md).

## Build

- Start with `gh stack init bead/<id>-<slug>` from the appropriate base; add a branch with `gh stack add bead/<id>-<slug>`.
- A bead blocked only by implementation beads already built and verified in your own stack may be claimed with `bd update <id> --claim` and built on top. Preserve its dependencies until integration. This exception never bypasses unanswered decisions, unmet acceptance criteria or another owner's unfinished work.
- `gh stack view` identifies the branch below for each PR's diff and checks. Use the default branch's approved role card as policy even when the diff base is another stack branch.
- Submit with `gh stack submit --auto --open`, then set each PR body with `gh pr edit <PR URL> --body-file pr.md`. Confirm each real URL and gate it once to its bead.
- Keep the stack reviewable. Follow the project's review cap; split independent work into a separate stack or PR when that reduces coupling.

## Maintain

Fix CI or review feedback on the affected branch, then rebase descendants and revalidate affected behavior. Use `gh stack rebase` and `gh stack push` only within the project's authorization; rewriting published history requires the applicable permission. Coordinate changes to branches others use.

A rejected PR does not merge as a formality. Revise it, or remove/rebase its dependents under the project's authorization, preserving any still-required outcome. Update the associated gates and bead status to match the actual PRs.

## Integrate

Merge only when authorized, normally bottom-up. Each merge resolves its gate; `close-merged.sh` closes beads whose PRs all merged. With the stack integrated, start the next independent work from the updated integration branch.
