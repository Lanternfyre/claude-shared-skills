#!/usr/bin/env bash
# beadwork SessionStart hook (also runs after /clear and compaction). Prints as session context:
#   - .beads/PRIME.md through `bd prime`, when the project has one;
#   - bd memories (short-lived agent context), unless BEADWORK_NO_MEMORIES=1;
#   - one status line: day/night, ready work, open questions, review queue, away switch.
# Silent in projects without a .beads/ workspace. Needs bd; jq for the ready count.
set -u
cd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || exit 0
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

tz=${BEADWORK_TZ:-Europe/Warsaw}
win=${BEADWORK_DAY:-08-23}
h=$(TZ=$tz date +%H)
if ((10#$h >= 10#${win%-*} && 10#$h < 10#${win#*-})); then mode=day; else mode=night; fi
role=${BEADWORK_ROLE:-}

jlen() { jq length 2>/dev/null || echo '?'; }
ready=$(bd --readonly ready ${role:+--label "role:$role"} --exclude-type epic,decision --json 2>/dev/null | jlen)
asked=$(bd --readonly count -l human ${role:+-l "asked-by:$role"} --status open 2>/dev/null || echo '?')
review=$(bd --readonly count --status in_review 2>/dev/null || echo '?')
away=$(bd --readonly list -l operator:away --json 2>/dev/null | jlen)

echo "beadwork: $mode ($tz $(TZ=$tz date +%H:%M)) · ready $ready · open questions $asked · in review $review${role:+ · role $role}"
if [ "$away" != 0 ] && [ "$away" != '?' ]; then
  echo "beadwork: the operator is AWAY. Start no new bead; finish or park the current one."
fi
