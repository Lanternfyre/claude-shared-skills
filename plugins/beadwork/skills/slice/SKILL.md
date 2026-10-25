---
name: slice
description: Work loop for a Beads-driven session. Claim the next ready bead, keep its lease alive, build it on a branch, verify, open the PR, hand it to review, repeat. Pass "night" for an unattended run.
argument-hint: "[night]"
disable-model-invocation: true
---

# The slice loop

- If `$ARGUMENTS` is `night`, this is an unattended run: also follow [night.md](night.md).
- Your role is in the session-start status line (`role <x>`). If the line names no role, any role's bead may be claimed. Leave out the role arguments below.
- **Write commands literally.** Fill each `<placeholder>` with its value. Don't use shell variables or `${…}` expansions: the permission check refuses them.
- The project's instructions win over this skill: its verify command, PR cap, must-ask list, who closes beads, and whether sub-agents are allowed.

## 1. Start checks (stop on any failure)

```bash
bd --readonly ping
bd --readonly list -l operator:away --json          # away switch: anything but [] means stop
```

## 2. Own questions first

```bash
bd --readonly list -t decision -l asked-by:<role> --all --json
```
- Apply any answer that arrived since your last session (the `question` skill, §6).
- By day, make sure every question you still need is asked before you take new work.

## 3. Claim

```bash
bd ready --label role:<role> --exclude-type epic,decision --claim --json
```
The output is the claimed bead, or `[]`. Its `id` is `<id>` from here on.

If nothing is ready for your role, never invent work. Report and stop:
- `bd --readonly ready --exclude-type epic,decision --json`: what is ready for other roles. `--explain` ignores filters, so don't use it here.
- `bd --readonly blocked`: what is waiting on what.

## 4. Keep the lease

Run `while sleep 120; do bd hb <id> || break; done` as a background command. Stop it when you hand off, park or block. If `bd hb` fails, the claim is gone: stop work on this bead.

## 5. Branch and read

- Branch `bead/<id>-<slug>` off a fresh default branch, or use a worktree.
- Read the project instructions, then `bd show <id>`, then every doc the bead links. Use the glossary's terms in code, tests and text.
- For a spike bead (`-t spike`), follow [spike.md](spike.md) instead of steps 6–7.
- For a bug bead (`-t bug`), follow [bug.md](bug.md) during step 6.

## 6. Work

- Stay inside the Guardrails. Anything outside them goes through the `question` skill (a decision) or becomes a surprise bead.
- Findings go to the bead first: `bd note <id> "…"` at each milestone. Notes survive compaction and handoff.
- `bd remember` is only for short-lived context the next sessions need, such as "staging DB down until Friday". Never use it for durable knowledge.
- If you hit a usage limit or the session is ending, park the bead: push to `HEAD:bead/<id>-wip`, `bd note`, then `bd unclaim <id> --reason "…"`.

## 7. Finish

1. Run the project's verify command. Open no PR unless it is green.
2. Check every Acceptance Criterion and note the evidence.
3. **Promote** what future work needs into Git docs, in this PR, with the `write` skill: architecture decisions → an ADR (the `adr` skill), constraints → `docs/architecture/`, domain rules → `docs/domain/`, terms → `docs/domain/glossary.md`. Notes that only mattered for this bead stay in the bead.
4. **Docs impact.** Decide what the change does to the docs: contract, behaviour, data, security, operations, architecture, or internal only. If any docs page changed, finish it with the `write` skill (its check and reader walkthrough). A security or public-contract change with no matching docs is `unknown`, never `none`.
5. `gh pr create`. The body has, in this order:
   - `Bead: <id>`;
   - what and why, in plain words;
   - the criteria evidence;
   - any provisional defaults it relies on;
   - the `Docs impact:` line, plus `Structure:` and `Readers:` if docs changed.
6. `bd update <id> --status in_review`, then stop the heartbeat.
7. **Never `bd close` a work bead.** It closes when its PR merges, via the project's steward or `/beadwork:review-chunk`.
8. Go back to step 2.

## Stop rules

- On a tripwire in the bead, or two red verify or CI runs you cannot explain:
  `bd update <id> --status blocked --append-notes "tripwire: …"`. File a surprise bead, stop the heartbeat, and stop.
- One bead at a time. No sub-agent fan-out unless the project allows it. The docs reader walkthrough (one fresh agent per docs change) is the standing exception.
