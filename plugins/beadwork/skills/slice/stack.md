# Stacked PRs within one bead

Use a stack when one bead needs several PRs to stay under the size cap. Each PR builds on the one below it, and the operator reviews them bottom-up. Work in a *different* bead never stacks on yours: it waits for your merge.

**Still a pilot.** `gh stack` is version 0.1.0. On the first beads that use it, record what worked and what didn't with `bd note <id>`.

Requires the extension: `gh extension install github/gh-stack`.

1. **Start** on the bead's first branch: `gh stack init bead/<id>-<slug>-1`. Commit the first reviewable step.
2. **Add** each further step as its own branch on top: `gh stack add bead/<id>-<slug>-2`, then commit. Each PR stays under the cap and makes sense on its own.
3. **Submit** with `gh stack submit`. It pushes every branch and opens or updates their PRs. Each PR body follows step 7.5 of the slice loop and says where it sits ("2 of 3").
4. **Gate** every PR in the stack, using step 7.6 with one `gh:pr` gate per PR URL.
5. **Review changes** are yours. Fix them on the branch they belong to, then run `gh stack rebase` and `gh stack push`. Never rebase another agent's branch.
6. **Merging** is the operator's: `gh stack merge` merges the stack atomically, or the operator merges bottom-up on GitHub. The gates resolve as each PR merges. Step 1 of the next session closes the bead once every gate has.

If the bottom PR is rejected, stop. File a decision bead (the `question` skill): rework the stack, or drop the steps above it.
