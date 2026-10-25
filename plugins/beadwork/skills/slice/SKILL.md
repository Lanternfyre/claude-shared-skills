---
name: slice
description: Work loop for a Beads-driven session. Close merged work, claim the next ready bead, keep its lease alive, build it on a branch, verify, open the PR behind a merge gate, repeat. Pass "night" for an unattended run.
argument-hint: "[night]"
disable-model-invocation: true
---

# The slice loop

- If `$ARGUMENTS` is `night`, this is an unattended run: also follow [night.md](night.md).
- Your role is in the session-start status line (`role <x>`). If the line names no role, any role's bead may be claimed: leave out `--label role:<role>` and `-l asked-by:<role>` below. Never leave out `--exclude-label human`, because those beads are the operator's own work.
- **Write commands literally.** Fill each `<placeholder>` with its value. Don't use shell variables or `${…}` expansions: the permission check refuses them.
- The project's instructions win over this skill: its verify command, PR cap, must-ask list, who closes beads, and whether sub-agents are allowed.

## 1. Start checks (stop on any failure)

```bash
bd --readonly ping
bd --readonly list -l operator:away --json          # away switch: not [] means hold questions as at night; work goes on
```

**Close merged work.** A bead under review waits behind one merge gate per pull request. When those gates resolve, the bead becomes ready again, so it must be closed before anyone claims it. Run:

```bash
${CLAUDE_PLUGIN_ROOT}/scripts/close-merged.sh
```
It runs the merge check, then closes every `pr-open` bead whose PRs have all merged. It repeats until nothing more closes, because a stack's beads close bottom-up. It removes the label only after a successful close, and flags a bead whose PR was closed unmerged as `pr-closed`, for the operator. If it exits non-zero, `gh` can't reach GitHub: run `gh auth status`, report what it says, and stop. Never close merged work by hand; the script exists because doing so went wrong.

**Your stack first.** Each box keeps one stack of PRs ([stack.md](stack.md)). `gh stack view` shows it. Before taking new work, look after it:
- **Red CI** on one of its PRs: fix it in that PR's own branch, then `gh stack rebase` and `gh stack push`.
- **Review feedback** (PR comments, or the operator asking): fix it in a new PR on top of the stack, gated to the same bead. Never rework a lower PR.
- **Conflicts** with the main branch: `gh stack rebase`, then `gh stack push`.

Details, limits and the denied-PR case are in [stack.md](stack.md).

## 2. Own questions first

```bash
bd --readonly list -t decision -l asked-by:<role> --all --json
```
- Apply any answer that arrived since your last session (the `question` skill, §6).
- By day, make sure every question you still need is asked before you take new work.

## 3. Claim

```bash
bd ready --label role:<role> --exclude-type epic,decision --exclude-label human --claim --json
```
The output is the claimed bead, or `[]`. Its `id` is `<id>` from here on.

If nothing is ready, a bead blocked **only by beads whose PRs are in your own stack** may still be claimed and built on top of them. `bd --readonly blocked --json` lists each bead's `blocked_by`. Claim one with `bd update <id> --claim`. Work blocked by anyone else's beads waits.

If nothing is claimable, never invent work. Report and stop:
- `bd --readonly ready --exclude-type epic,decision --exclude-label human --json`: what is ready for other roles. `--explain` ignores filters, so don't use it here.
- `bd --readonly blocked`: what is waiting on what.

## 4. Keep the lease

Run `while sleep 120; do bd hb <id> || break; done` as a background command. Stop it when you hand off, park or block. If `bd hb` fails, the claim is gone: stop work on this bead.

## 5. Branch and read

- **Branch on your stack:** `gh stack add bead/<id>-<slug>` puts the new branch on top of your open stack. With no open stack (the operator merged it), start one from a fresh default branch: `gh stack init bead/<id>-<slug>`.
- Read the project instructions, then your role card at `.claude/roles/<role>.md` (its purpose and never list bind you), then `bd show <id>`, whose notes are the bead's current state, then `bd comments <id> --json`. Comments added since your last update steer you: an operator's comment (its author is `operator`) binds you, like a Guardrail. This needs agents to write under their own name (the box's `BEADS_ACTOR`). In an operator's own session, the agent's comments are `operator` too, so skip the ones you wrote. Then read every doc the bead links. Use the glossary's terms in code, tests and text. With no role there is no card, and only the project's rules apply.
- For a spike bead (`-t spike`), follow [spike.md](spike.md) instead of steps 6–7.
- For a bug bead (`-t bug`), follow [bug.md](bug.md) during step 6.

## 6. Work

- Stay inside the Guardrails. Anything outside them goes through the `question` skill (a decision) or becomes a surprise bead.
- **Progress record.** At each milestone (a test passing, a design choice made, a PR opened) and whenever you park:
  1. Replace the current state: `bd update <id> --notes "<the current state>"`. Keep it short, in this shape:
     ```text
     Branch: bead/<id>-<slug> @ <short sha> (pushed)
     Done: [x] <step>  [x] <step>
     Next: <one concrete action>     Then: [ ] <step>  [ ] <step>
     Blocked by: <question ids, a red check, a missing fact, or nothing>
     Tried and failed: <dead ends, so nobody repeats them>
     ```
     The checklist in it is the bead's plan; there are no subtask beads.
  2. Log the update as a comment: `bd comments add <id> "<what changed since the last update>"`. Comments carry their author and time, and they are the history.
  Findings worth keeping beyond this bead still go into the docs at Finish (step 3).
- `bd remember` is only for short-lived context the next sessions need, such as "staging DB down until Friday". Never use it for durable knowledge.
- If you hit a usage limit or the session is ending, park the bead: push to `HEAD:bead/<id>-wip`, write the progress record (both steps) so the next session can continue from it, then `bd unclaim <id> --reason "…"`.

## 7. Finish

1. Run the project's verify command. Open no PR unless it is green.
2. Check every Acceptance Criterion and note the evidence.
3. **Promote** what future work needs into Git docs, in this PR, with the `write` skill: architecture decisions → an ADR (the `adr` skill), constraints → `docs/architecture/`, domain rules → `docs/domain/`, terms → `docs/domain/glossary.md`. Notes that only mattered for this bead stay in the bead.
4. **Docs impact.** Decide what the change does to the docs: contract, behaviour, data, security, operations, architecture, or internal only. If any docs page changed, finish it with the `write` skill (its check and reader walkthrough). A security or public-contract change with no matching docs is `unknown`, never `none`.
5. **Role fence.** With a role, `${CLAUDE_PLUGIN_ROOT}/scripts/role-check.sh .claude/roles/<role>.md` must pass before any PR opens. It lists files outside the card's paths, judged by the card as the main branch has it. Move such a change out of the PR, or raise it through the `question` skill. Never edit the card to fit.
6. **Open the PR on the stack:** `gh stack submit --auto --open`, then `gh pr edit <PR URL> --body-file pr.md` for each new PR. A bead that needs more than one PR to stay under the size cap adds a branch per PR in the same way. Each PR body has, in this order:
   - `Bead: <id>`;
   - what and why, in plain words;
   - the criteria evidence;
   - any provisional defaults it relies on;
   - the `Docs impact:` line, plus `Structure:` and `Readers:` if docs changed.
7. **Hand it to review.** Give each PR a merge gate, then release the bead:
   ```bash
   bd gate create --type=gh:pr --blocks <id> --await-id <PR URL> --reason "PR #<n>"   # one per PR
   bd label add <id> pr-open
   bd unclaim <id> --reason "in review: <PR URL>"
   ```
   Then stop the heartbeat. The gates keep the bead out of `bd ready` until every PR merges. Always use the full PR URL, so the check works from any repo.
   **Gate only a real PR.** If submitting printed no PR URL for your branch (check `gh stack view`), create no gate and add no label. Run `gh auth status`, keep the bead claimed, and stop.
8. **Never `bd close` unmerged work.** The bead closes after its PRs merge, at step 1 of whichever session runs next, or through the project's steward.
9. Go back to step 1.

## Stop rules

- On a tripwire in the bead, or two red verify or CI runs you cannot explain:
  `bd update <id> --status blocked --append-notes "tripwire: …"`. File a surprise bead, stop the heartbeat, and stop.
- One bead at a time. No sub-agent fan-out unless the project allows it. The docs reader walkthrough (one fresh agent per docs change) is the standing exception.
