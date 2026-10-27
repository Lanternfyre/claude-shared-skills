# Continue or refresh a worker conversation

Use this reference when `BEADWORK_MANAGED=1`. A small runner owns process lifecycle, the exact claim and heartbeat; the agent owns implementation and chooses useful conversation boundaries. Attended and unattended runs use the same protocol. Host auto-compaction does not change the bead or ownership.

## Work and checkpoint

Read `BEADWORK_BEAD`, its current notes and the actual checkout before editing. The runner supplies a unique `BEADS_ACTOR` and a fixed `BEADWORK_RUN_DEADLINE`; starting a fresh conversation never extends that deadline. Do not claim a second bead or create a separate heartbeat. Before the park-by time, finish a safe handoff or save resumable progress.

Before returning to the runner, stop or integrate delegates, save work, and update the bead's current progress record, including the branch/worktree, delivery method, decisions, evidence and next step. While still owning the bead, record this turn's checkpoint:

```bash
bd update <id> --if-assignee <actor> --set-metadata beadwork_checkpoint=<BEADWORK_CHECKPOINT>
```

Then deliver or park using the normal workflow, or retain the claim with outcome `working` to continue the same bead. Check the user's latest steering before delivery. Never copy the entire conversation into notes; keep what a replacement worker needs and link durable findings.

## Choose the next conversation

Return one final JSON object, with no surrounding prose:

```json
{"bead":"<id>","outcome":"working","ref":null,"next":"fresh","delegates_stopped":true,"checkpoint":"<BEADWORK_CHECKPOINT>"}
```

`next` is `continue` to retain useful context, `fresh` to start clean, or `stop` to end this run. Choose from the work, not a fixed number of beads. A CLI process can exit and be resumed with the same conversation ID; that is still the same conversation.

| Outcome | Durable state before returning | `ref` |
|---|---|---|
| `working` | This worker still owns the bead; progress and checkpoint saved | `null` |
| `pr` | Actual PR gate plus `pr-open`, claim released | PR URL |
| `review` | Blocked, unassigned, `integration-pending` | Saved commit |
| `complete` | Acceptance verified, required integration completed, bead closed | Integrated commit |
| `parked` | Saved resumable work, claim released and bead open | `null` |
| `blocked` | Blocker recorded, claim released and bead blocked | `null` |

The runner verifies the checkpoint, ownership and recorded handoff before proceeding. It does not replace acceptance tests, review or integration evidence. Never mark delegates stopped while they can still write.

## Recovery

A clean handoff can resume from its saved state. After an unclean stop, inspect the runner's state and logs, exact bead and checkout. Establish that old writers have stopped and reconcile ownership before restarting. Do not steal another worker's claim or clear an unresolved recovery marker just to make a run start. Record recovery facts in the bead. The runtime guide documents the supported recovery commands.

For a safely parked run launched with an explicit `--bead`, resolve the blocker and use `--recover` in the same worktree before the original deadline. The runner rechecks the saved checkpoint and readiness before reclaiming that bead; a plain restart does not reclaim it.
