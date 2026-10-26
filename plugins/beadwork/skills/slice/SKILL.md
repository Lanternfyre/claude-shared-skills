---
name: slice
description: 'Work an authorized outcome through Beads: claim, build or delegate, verify, deliver, and preserve enough state to resume. Pass "night" for an unattended run.'
argument-hint: "[night]"
disable-model-invocation: true
---

# The slice loop

Use the [host runtime guide](../../runtime.md) for invocation, helper paths and startup context.

Assume Beads and the project's skills are installed. Check the services needed for this task; do not repeat onboarding. User instructions and existing authorization take precedence over this workflow and project defaults.

- With `$ARGUMENTS` = `night`, also read [night.md](night.md).
- The session-start line supplies the role. With no role, omit `--label role:<role>` and `-l asked-by:<role>` below. Always exclude `human` beads from agent claims.
- Use literal arguments in environments whose permission checks require them. The commands below are examples with placeholders, not a ban on ordinary shell scripting.
- Delivery follows the project: `BEADWORK_DELIVERY=pr` (default), `stack`, or `local`. Read [delivery.md](delivery.md) for the selected mode. This selects mechanics; it does not authorize pushing or merging.

## 1. Orient

```bash
bd --readonly ping
bd --readonly list -l operator:away --json
```

Read the project instructions and role card, if any. Their explicit prohibitions and protected paths bind you; expected paths are guidance. An away operator means hold questions for later, not stop work.

For PR delivery, run `"<plugin-root>/scripts/close-merged.sh"` before claiming work. It resolves merge gates, closes merged beads and flags closed-unmerged PRs. If it fails, leave uncertain review beads alone, report the failure and diagnose it. Continue independent work whose claim and dependencies can be verified; a GitHub outage need not stop local implementation. Do not claim `pr-open` or `pr-closed` beads as new work, or close them manually.

Identify your existing delivery branches needing attention: failing CI, review feedback and conflicts. Claim the corresponding bead and keep its lease before editing, retaining its review gates. Fix the affected branch and revalidate the relevant changes. This is maintenance of known work, not permission to bypass another owner's claim. In stack mode also read [stack.md](stack.md).

## 2. Apply answers

```bash
bd --readonly list -t decision -l asked-by:<role> --status open --json
```

Apply available answers using the `question` skill (§6). Post needed questions during the day, or store them when away. Continue authorized work while answers are pending; a question blocks only the work that requires its answer.

## 3. Claim

```bash
bd ready --label role:<role> --exclude-type epic,decision --exclude-label human,pr-open,pr-closed --claim --json
```

The returned bead id is `<id>`; `<actor>` is its actual assignee, used in guarded handoffs. If nothing is ready, inspect `bd --readonly blocked --json`. Stack mode may build on satisfied implementation dependencies in your own stack (see [stack.md](stack.md)); unanswered decisions and other owners' unfinished work remain blockers.

If an approved plan still needs decomposition, create its next verifiable slices with the `bead` skill. Otherwise report the blockers and stop; do not invent goals to fill the queue.

## 4. Own the work

Keep the lease alive, for example with `while sleep 120; do bd hb <id> || break; done` in the background, and observe its exit/failure while working. On a heartbeat failure, stop writes by you and your delegates and inspect ownership read-only. Resume only if ownership is confirmed. Otherwise preserve the checkout and report its location and recovery context in the session; do not update or unclaim another owner's bead. The parking procedure below applies only while you still own the claim. Stop the heartbeat at handoff or release.

Read `bd show <id>`, its current notes, new comments and the relevant linked docs. Operator comments steer the task. Preserve their source and do not treat your own comments as new operator instructions. Read the needed glossary entries, not the entire knowledge base by default.

Create or resume the delivery branch. For bugs read [bug.md](bug.md); for experiments read [spike.md](spike.md).

**Delegation is allowed unless the project forbids it.** The owner may build directly or coordinate implementation and review agents. Give each delegate a bounded outcome, relevant context, allowed writes and expected evidence. Use isolated worktrees for independent writes, or non-overlapping files with serialized Git operations in a shared checkout. Serialize tools that mutate the same resources, including mutation tests. The owner keeps the lease, integrates results, checks the combined behavior and updates the bead. Delegation does not grant broader permissions. Stop or hand off delegates before releasing ownership.

Use as many agents as the task and available budget justify; no fixed count is required. Do not create beads for internal steps unless they need independent ownership, scheduling or acceptance.

## 5. Plan and build

Record an approach before substantial implementation; a small fix needs only a sentence. Add alternatives and risks when they affect a decision. Start once the plan is recorded: planning is not another approval gate.

Re-plan as evidence changes. You may re-cut within the approved outcome, preserving all acceptance criteria and dependencies (`bead` skill). Necessary adjacent fixes may extend expected paths if they preserve the contract and cross no explicit protection. Explain the expansion and its verification. Unrelated improvements become follow-up beads.

**Keep one current progress record.** Update `bd update <id> --notes "<state>"` at meaningful checkpoints and before handoff, compaction or stopping. Include what another session needs:

```text
Branch/worktree: <location and commit; local or pushed>
Plan: <approach and any consequential choice>
Done / evidence: <completed outcomes and checks>
Next: <concrete action>
Blocked / failed attempts: <only what matters>
Delegates: <active work and integration state, if any>
```

Use comments for decisions, operator communication or a useful historical change; do not duplicate every progress update in a comment. Keep execution status in Beads rather than parallel handover files. Durable findings belong in docs; `bd remember` is for short-lived context shared across tasks.

To park resumable work you still own, stop delegates, save work on the named branch (push WIP only if authorized), write the progress record, then `bd unclaim <id> --if-assignee <actor> --reason "…"` and stop the heartbeat. State explicitly if work is only local so the next session uses the right checkout. For blocked work without a dependency, use a guarded update that clears the assignee and sets `blocked` together; `unclaim` resets status to open.

## 6. Verify and deliver

1. Run the required project checks and verify every Acceptance Criterion. Use affected checks while iterating; run the required delivery gates before review or integration. Do not weaken checks to make the work pass.
2. Promote durable findings and update affected documentation with the `write` skill. Use an ADR only when the `adr` skill's decision test fits. Record `Docs impact: updated (…) | needs review (…) | unknown (…) | none`. A security or public-contract change without checked documentation is `unknown`, never `none`.
3. Check scope. With a role, run `"<plugin-root>/scripts/role-check.sh" "<role-card>" <diff-base> <policy-ref>`: use the default branch for policy and the actual PR base for the diff. Outside expected paths is advisory: explain why the change is necessary and how it was checked. Protected paths require explicit authorization. A failure is not permission to edit the role card to pass; existing explicit authorization can be recorded as an exception. If the checker is unavailable, inspect the same diff against the approved card and report the limitation.
4. Review the actual diff for regressions, missing criteria and unintended changes. Use an independent reviewer for substantial or risky changes when available; a small mechanical edit can use a direct review. Follow project-required review tools when available, but a missing optional skill is not a reason to stop. Fix valid findings; explain deferred findings. Rerun checks affected by fixes and any project-required delivery gates.
5. Deliver using [delivery.md](delivery.md). Record the bead id, what changed and why, acceptance evidence, material decisions/defaults, scope exceptions, review findings and docs impact. If docs changed, report structure and reader checks separately. Keep this in the PR body, or the bead for local delivery.
6. Release only after the handoff state is durable. PR delivery requires a real merge gate for each real PR; local delivery requires verified integration or an explicit pending-integration state. Do not close work merely because implementation finished.
7. Continue to the next authorized outcome. Night sessions instead emit their result and exit.

## When progress stops

A tripwire, lost ownership, protected action without authorization, or genuinely missing input blocks the affected work. Record the evidence and what would unblock it, release safely and take independent work when available. Stop the whole run only when the constraint applies to the whole run.

A red check is feedback, not a fixed attempt budget. Continue while new evidence supports a concrete next step within the time/resource budget. If attempts repeat without new evidence, park with the failed approaches and ask or file a follow-up. Do not spin indefinitely or bypass failing gates.
