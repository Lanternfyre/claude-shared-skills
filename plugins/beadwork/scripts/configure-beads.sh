#!/usr/bin/env bash
# Apply the beadwork conventions to the Beads workspace of the current repo.
# Idempotent; run once per project after `bd init`. Most values land in .beads/config.yaml
# (commit it); status.custom lands in the project database.
set -euo pipefail
bd --readonly ping >/dev/null

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
