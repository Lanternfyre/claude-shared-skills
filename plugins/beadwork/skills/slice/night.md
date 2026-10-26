# Night session (unattended)

The night runner starts one fresh session per bead. `BEADWORK_ENGINE=claude` (default) invokes `/beadwork:slice night`; `BEADWORK_ENGINE=codex` invokes `codex exec` with the exact installed slice skill path and night arguments. Both share the cutoff, review cap, verify command, role's `night: yes`, eligible `night-ok` work, usage budget and repeated session failure rules. **One night session handles one bead, then exits.** This bounds unattended execution; a bead may span sessions.

Role cards resolve from `BEADWORK_ROLE_CARD`, then `BEADWORK_ROLE_DIR/<role>.md` when set, then `.beads/roles/<role>.md` if present, otherwise `.claude/roles/<role>.md`. Claude reads `model`/`effort`; Codex requires `codex_model` and optionally `codex_effort` (`low`, `medium`, `high` or `xhigh`). Codex settings never fall back to Claude aliases or effort levels. Codex runs in the workspace-write sandbox with normal trust and approval rules. If its startup context is absent, run the installed plugin's `hooks/session-start.sh` as directed by the runner and read the output before claiming work; do not bypass trust or approvals to do so.

Without an explicit card or directory override, the runner stops if the resolved card path differs from an existing default-branch role card. Review a move between neutral and legacy role directories before unattended execution; adding or deleting a worktree card cannot replace approved night permissions or model settings. At the approved path, night settings come from the default branch.

1. Orient and apply available answers as by day. Follow `BEADWORK_DELIVERY` (`pr`, `stack` or `local`); local mode needs no GitHub sweep. The away switch holds questions, not work.
2. Claim with `--label night-ok` in addition to the role and normal exclusions. In stack mode, this also applies to work built on your own verified stack. If nothing is claimable, emit `BEADWORK-NIGHT: nothing - -`.
3. Work and delegate as by day. The owner keeps the lease, integrates results, verifies and records the handoff. Only the parent emits the night status line; delegates finish or stop before the session exits.
4. **Unattended boundaries:** do not merge PRs, push to the default branch, change live/shared systems, destroy shared data/history, or change secrets/permissions. Local integration requires explicit project authorization for unattended integration. Tests in isolated databases and ordinary CI/workflow source changes are allowed when within the task's authority; changing deployed permissions is a separate action. Changes to instructions or skill source are reviewable work, not permission to relax this session's governing rules. Explicit project prohibitions still apply.

   The checkout's pre-push guard refuses default-branch pushes and remote branch deletions. It does not enforce the other boundaries.
5. **Park before the time box.** The status line gives `park by <time>` in UTC, a quarter of the time box before expiry. Check `date -u +%FT%H:%MZ` at meaningful checkpoints and before delivery. Once past it, stop starting work, gather delegates' state and park. If a PR or integration handoff already exists, finish recording its gate/status and release instead. If the process times out first, the runner stops: reconcile delegates, ownership and checkout before restarting. It does not guess which bead to unclaim. Task notes must make recovery possible.
6. **Questions:** store unresolved operator choices as `auq_card` metadata for the morning/steward; do not wake the operator. Routine implementation decisions need no card. For `default-ok`, record the default and continue. For `must-ask`, finish independent work, then park with the blocking dependency and current state.
7. **Emit exactly one result in the final response**, then exit. Codex results come from its final-message file; transcript echoes do not count. The runner files the morning summary:
   - `BEADWORK-NIGHT: pr <id> <PR URL>`: handed to PR review.
   - `BEADWORK-NIGHT: fixed <id> <PR URL>`: maintained existing PR work.
   - `BEADWORK-NIGHT: complete <id> <commit>`: verified local integration, bead closed.
   - `BEADWORK-NIGHT: review <id> <commit>`: saved locally, blocked and labelled `integration-pending`.
   - `BEADWORK-NIGHT: parked <id> -`: resumable work, including a pending required answer or time limit.
   - `BEADWORK-NIGHT: blocked <id> -`: tripwire or no evidence-based next step within budget.
   - `BEADWORK-NIGHT: nothing - -`: no eligible work.
