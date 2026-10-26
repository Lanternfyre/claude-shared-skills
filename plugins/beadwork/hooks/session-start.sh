#!/usr/bin/env bash
# beadwork SessionStart hook (also runs after /clear and compaction). Prints as session context:
#   - .beads/PRIME.md through `bd prime`, when the project has one;
#   - bd memories (short-lived agent context), unless BEADWORK_NO_MEMORIES=1;
#   - availability, ready work, questions, both review queues and the exact active bead;
#     and the away switch.
# Silent in projects without a .beads/ workspace. Needs bd; jq for the ready count.
set -u
cd "${BEADWORK_PROJECT_DIR:-${CLAUDE_PROJECT_DIR:-$PWD}}" 2>/dev/null || exit 0
[ -d .beads ] && command -v bd >/dev/null 2>&1 || exit 0

if ! bd --readonly ping >/dev/null 2>&1; then
  echo "beadwork: Beads server unreachable. Do not claim, file or close beads until \`bd ping\` is ok."
  exit 0
fi

mem=--no-memories
if [ "${BEADWORK_NO_MEMORIES:-0}" != 1 ] &&
   bd --readonly memories --json 2>/dev/null | jq -e 'del(.schema_version) | length > 0' >/dev/null 2>&1; then
  mem=
fi
if [ -f .beads/PRIME.md ]; then
  bd --readonly prime $mem
elif [ -z "$mem" ]; then
  bd --readonly prime --memories-only
fi

mode=${BEADWORK_MODE:-attended}
role=${BEADWORK_ROLE:-}

jlen() { jq length 2>/dev/null || echo '?'; }
ready=$(bd --readonly ready ${role:+--label "role:$role"} --exclude-type epic,decision --exclude-label human,pr-open,pr-closed --json 2>/dev/null | jlen)
asked=$(bd --readonly count -l human ${role:+-l "asked-by:$role"} --status open 2>/dev/null || echo '?')
review=$(bd --readonly list --label-any pr-open,integration-pending --limit 0 --json 2>/dev/null |
  jq '[.[] | select(.status != "closed")] | unique_by(.id) | length' 2>/dev/null || echo '?')
away=$(bd --readonly list -l operator:away --json 2>/dev/null | jlen)

park=${BEADWORK_PARK_BY:+ · park by $BEADWORK_PARK_BY}  # set by the runner
echo "beadwork: $mode · ready $ready · open questions $asked · in review $review${role:+ · role $role}$park"
if [ -n "${BEADWORK_BEAD:-}" ]; then
  echo "beadwork: active bead $BEADWORK_BEAD · worker ${BEADS_ACTOR:-unset} · checkout $PWD"
  if [ "${BEADWORK_MANAGED:-}" = 1 ]; then
    echo "beadwork: the runner owns this claim and heartbeat. Inspect this bead before writing; do not claim another bead."
  fi
  bd --readonly show "$BEADWORK_BEAD" --json 2>/dev/null |
    jq -er --arg id "$BEADWORK_BEAD" '(if type == "array" then .[] else . end) |
      select(.id == $id) | "Status: \(.status); assignee: \(.assignee // "unassigned")\nProgress: \(.notes // "No saved progress; inspect the task and checkout.")"' ||
    echo "beadwork: cannot reload the active bead; verify its ownership before writing."
fi
card=${BEADWORK_ROLE_CARD:-}
if [ -z "$card" ]; then
  if [ -n "${BEADWORK_ROLE_DIR:-}" ]; then card="$BEADWORK_ROLE_DIR/$role.md"
  elif [ -f ".beads/roles/$role.md" ]; then card=".beads/roles/$role.md"
  else card=".claude/roles/$role.md"; fi
fi
if [ -n "$role" ]; then
  if [ -f "$card" ]; then echo "beadwork: role card $card"
  else echo "beadwork: routing role $role has no card at $card; follow the project instructions."; fi
fi
script="$(cd "$(dirname "$0")/.." && pwd)/scripts/configure-beads.sh"
want=$(sed -n 's/^CONFIG_VERSION=//p' "$script" 2>/dev/null)
have=$(bd --readonly config get custom.beadwork-config-version 2>/dev/null | tail -1)
if [ -n "$want" ] && [ "$have" != "$want" ]; then
  echo "beadwork: this repo's Beads settings predate the skills (want version $want). Run $script in the main checkout, then commit .beads/config.yaml."
fi
if [ "$away" != 0 ] && [ "$away" != '?' ]; then
  echo "beadwork: the operator is AWAY: queue questions and continue independent authorized work. Explicit current availability overrides this default."
fi
