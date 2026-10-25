---
name: review-chunk
description: Digest of the PRs waiting for operator review, each in plain words with its risk, evidence and provisional defaults, in a suggested order. Also closes beads whose PRs have merged.
disable-model-invocation: true
---

# Review chunk

## 1. Close merged work

Skip this step if the project has a steward that closes beads on merge.

For each bead in `bd --readonly list --status in_review --json`, find its PRs:
`gh pr list --state all --search "\"Bead: <id>\" in:body" --json number,state,mergeCommit`
- **All merged:** `bd gate check --type=gh` (if the project uses PR gates), then `bd close <id> --reason "merged #<n> <sha>"`.
- **Closed without merging:** `bd update <id> --status open --add-label pr-closed`.

## 2. Collect

```bash
gh pr list --state open --json number,title,url,body,isDraft,additions,deletions,files,statusCheckRollup
```
Keep the PRs whose body has a `Bead:` line and that are not drafts.

## 3. Digest each PR

- **What and why:** two lines in plain words, taken from the bead's Task and the PR body. Not a diff summary.
- **Risk:** low, med or high, and why: what could break, how far it reaches, what can't be undone.
- **Evidence:** CI status, acceptance criteria → tests, the demo link.
- **Provisional defaults** it relies on: decision beads labelled `provisional`.
- **Size:** hand-written lines, kept apart from tests, fixtures and generated files. Add the review class if the project uses one.

## 4. Order

1. PRs that unblock other work.
2. High-risk PRs, while attention is fresh.
3. Small, low-risk PRs last; they can be approved as a batch.

Flag PRs that touch the same files, so they are reviewed together.

## 5. Output

Print the digest here: one table (PR, risk, size, CI), then the bullets for each PR in the suggested order. When this runs without the operator in the session, post it as one auq card instead.
