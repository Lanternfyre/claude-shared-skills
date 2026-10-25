# One stack per box

Every PR a box opens goes on top of its one open stack until the operator merges. This applies to attended runs and nights alike. The point is an easy merge: the box never conflicts with itself, and the operator merges its work as one unit. Requires the extension: `gh extension install github/gh-stack`.

**Still a pilot.** `gh stack` is version 0.1.0. Record with `bd note <id>` what worked and what didn't.

## Building

- **Start:** with no open stack, branch the bead from a fresh default branch with `gh stack init bead/<id>-<slug>`. An existing unmerged PR branch can be adopted as the bottom: `gh stack init <its branch>`, then `gh stack add` on top.
- **Add:** each new bead, or each further PR of a big bead, is `gh stack add bead/<id>-<slug>`. The bead does not have to depend on the ones below.
- **Building on your own unmerged work:** a bead blocked only by beads whose PRs are in your stack may be claimed and stacked on top of them. A bead blocked by anyone else's beads waits for their merge.
- **Submit:** `gh stack submit --auto --open` opens or updates every PR in the stack. Then set each new PR's body (`gh pr edit <PR URL> --body-file pr.md`), saying where it sits ("3 of 4"), and gate it to its bead.
- **No height limit** beyond the project's review cap.

## Looking after it

- **Red CI:** fix it in the PR where it broke (`gh stack checkout <branch>`, fix, commit), then `gh stack rebase` and `gh stack push` so everything above follows. A fix on top would not turn that PR's own checks green. After two failed tries, mark that bead blocked with its findings and stop stacking.
- **Review feedback**, from PR comments or the operator's request: never rework a lower PR. Claim the bead again, fix it in a new PR on top, and gate that PR to the same bead. The bead closes when all its PRs have merged.
- **A denied PR** merges with the stack, and is undone by a revert in a new PR on top, gated to its bead.
- **Conflicts with the main branch** after other merges: `gh stack rebase`, then `gh stack push`. Only this box's stack branches. Never the main branch, never another box's branches.

## Merging

Merging is the operator's: the whole stack with `gh stack merge`, or bottom-up on GitHub. Each merge resolves its gate, and step 1 of the next session closes beads whose PRs have all merged. Once the stack is merged, the next bead starts a new stack.
