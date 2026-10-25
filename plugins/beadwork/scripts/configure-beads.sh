#!/usr/bin/env bash
# Apply the beadwork conventions to the Beads workspace of the current repo.
# Idempotent: run it after `bd init`, and again whenever the session-start line says the
# settings are out of date. The lint values land in .beads/config.yaml (commit it); the
# version stamp lands in the project database.
set -euo pipefail

# Bump when a setting below changes, so the session-start hook can tell a repo that its
# Beads settings no longer match the skills. 2: decision sections follow bd's built-ins;
# no in_review status (beadwork 0.4).
CONFIG_VERSION=2

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

bd config set custom.beadwork-config-version "$CONFIG_VERSION"
