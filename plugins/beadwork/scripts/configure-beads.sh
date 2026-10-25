#!/usr/bin/env bash
# Apply the beadwork conventions to the Beads workspace of the current repo.
# Idempotent; run once per project after `bd init`. Most values land in .beads/config.yaml
# (commit it); status.custom lands in the project database.
set -euo pipefail
bd --readonly ping >/dev/null

# Inside a git worktree, bd resolves .beads/ to the MAIN checkout and writes its
# config.yaml there, silently editing whatever branch that checkout is on.
if [ "$(bd --readonly context --json | jq -r '.is_worktree')" = true ]; then
  echo "configure-beads: refusing to run in a git worktree; bd would write the main checkout's .beads/config.yaml." >&2
  echo "Run it in the main checkout, or edit .beads/config.yaml in this worktree by hand." >&2
  exit 1
fi

# Sections the `bead` and `question` skills write. bd's built-ins add Acceptance Criteria
# (task, bug), Steps to Reproduce (bug), Success Criteria (epic), and Decision, Rationale
# and Alternatives Considered (decision) on top.
bd config set lint.sections.task     "Task, Guardrails"
bd config set lint.sections.bug      "Task, Guardrails"
bd config set lint.sections.chore    "Task, Guardrails, Acceptance Criteria"
bd config set lint.sections.spike    "Task, Guardrails, Variants, Measurements, Acceptance Criteria"
bd config set lint.sections.decision "Question, Default, If overturned, Level"
bd config set lint.sections.epic     "Goal, Scope, Tripwires"
bd config set validation.on-create   error

# Memories are short-lived agent context; cap what each session start injects.
bd config set prime.max-memory-chars 2000

# bd's anonymous usage metrics go to an external endpoint (user-level setting).
bd metrics off
