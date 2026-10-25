---
name: review-chunk
description: Digest of the PRs waiting for operator review, each in plain words with its risk, evidence and provisional defaults, in a suggested order. Also closes beads whose PRs have merged.
disable-model-invocation: true
---

# Review chunk

## 1. Close merged work

Do exactly what step 1 of the `slice` skill does under "Close merged work": run the merge check, then close every `pr-open` bead whose PRs have all merged. Beads labelled `pr-closed` go into the digest, because each one needs a decision.

## 2. Collect

The open merge gates are the review queue:
```bash
bd --readonly gate list --json          # each open gh:pr gate's await_id is a PR URL
```
For each PR URL: `gh pr view <PR URL> --json number,title,url,body,isDraft,additions,deletions,files,statusCheckRollup`. Skip drafts. Group PRs that belong to one stack, and review them bottom-up.

## 3. Digest each PR

- **What and why:** two lines in plain words, taken from the bead's Task and the PR body. Not a diff summary.
- **Risk:** low, med or high, and why: what could break, how far it reaches, what can't be undone.
- **Evidence:** CI status, acceptance criteria → tests, the demo link.
- **Provisional defaults** it relies on: decision beads labelled `provisional`.
- **Size:** hand-written lines, kept apart from tests, fixtures and generated files. Add the review class if the project uses one.
- **Docs:** the PR's `Docs impact`, `Structure` and `Readers` lines as written. Flag `unknown` impact and failed reader tasks. Flag critical pages (architecture, security, destructive runbooks, business claims, external-facing) as needing your own read.

## 4. Order

1. PRs that unblock other work.
2. High-risk PRs, while attention is fresh.
3. Small, low-risk PRs last; they can be approved as a batch.

Flag PRs that touch the same files, so they are reviewed together.

## 5. Output

Print the digest here: one table (PR, risk, size, CI), then the bullets for each PR in the suggested order. When this runs without the operator in the session, post it as one auq card instead.
