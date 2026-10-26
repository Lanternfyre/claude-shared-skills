# Delivery modes

`BEADWORK_DELIVERY=auto` is the default. Choose delivery from the project's conventions and the work's dependencies; record the choice in the bead's progress. No question is needed for ordinary delivery mechanics within existing authorization. Explicit `pr`, `stack` or `local` settings override automatic choice for new work. Mode is not authorization for external actions; instructions such as "never push" still apply.

| Situation | Delivery |
|---|---|
| Existing bead/branch | Preserve its recorded method |
| Independent change with PR review | Independent PR |
| Dependent changes benefiting from separate reviews | Stack, when the project's tools support it |
| Project uses local milestone integration | Local integration under its existing authorization |

Use an independent PR as the fallback. Unavailable GitHub access may delay publication without stopping useful local implementation; it does not silently change the agreed delivery or permit closing unintegrated work.

When resuming work, preserve its recorded branch and delivery mode. A default change does not authorize migrating an open stack or turning local work into a remote PR.

## Independent PRs (`pr`)

Start a branch from the appropriate integration branch, normally the default branch. Resume an existing bead branch when continuing work. Open or update its PR after the required checks. Fix review feedback on that branch; a new PR is needed only for genuinely separate work or a project convention.

For each actual PR URL, create a gate once:

```bash
bd gate create --type=gh:pr --blocks <id> --await-id <PR URL> --reason "PR #<n>"
bd label add <id> pr-open
bd unclaim <id> --reason "in review: <PR URL>"
```

Check existing gates before retrying a partial handoff. If submission failed, inspect whether the PR exists before retrying; never create a gate from an assumed URL. Save progress and park if delivery remains unavailable.

Merge only under the project's explicit authorization. `close-merged.sh` closes the bead after every PR merged. A PR closed without merging remains unresolved work; revise, replace or cancel it under the existing task authority. Never merge a rejected change merely to revert it later.

## Stacked PRs (`stack`)

Use [stack.md](stack.md). The gate and closure rules above still apply. Pick stacks for real dependencies or the project's review convention; independent beads do not have to share a stack.

## Local integration (`local`)

Use the project's branch and commit conventions. No GitHub access, remote push or PR gate is required. This mode does not itself authorize merging into the integration branch.

- If integration is authorized and its checks pass, integrate and record the resulting commit plus acceptance evidence; then close the bead.
- If implementation is complete but integration still needs review/authorization, stop delegates and record the branch, commit, evidence and who must act. Hand off atomically with `bd update <id> --if-assignee <actor> --status blocked --assignee "" --add-label integration-pending`, then stop the heartbeat. It remains open and unavailable for fresh claims. Do not use `bd unclaim` here: it resets status to open. If the installed CLI lacks guarded updates, retain the claim and report the required handoff instead of briefly exposing the bead as ready.
- When integration is authorized, resume that bead, integrate, verify the resulting state, remove `integration-pending` and close it. Never silently reset or replace another owner's changes.

The runner counts both `integration-pending` and `pr-open` beads against one review cap, deduplicated by bead ID. Its `complete` result means verified local integration; `review` means saved work awaiting integration.
