#!/usr/bin/env bash
# Close every bead whose pull requests have all merged. Step 1 of the work loop, the review
# digest and the night loop all run this.
#
#   close-merged.sh
#
# It runs the gh:pr gate check, then closes each pr-open bead whose every gh:pr gate closed
# as merged. It repeats until a pass closes nothing, because Beads refuses to close a bead
# while one it depends on is open, and a stack's beads depend on the ones below them.
# pr-open comes off only after a successful close. A bead whose PR was closed without merging
# loses pr-open, gets pr-closed, and stays open for the operator.
#
# Prints one line per bead closed or flagged. Exits 1, closing nothing, when the gate check
# reports errors: then gh cannot reach GitHub, and "nothing merged" cannot be told apart.
set -u

out=$(bd gate check --type=gh 2>&1); rc=$?
printf '%s\n' "$out" | tail -1
if [ "$rc" -ne 0 ] || printf '%s' "$out" | grep -Eq '\b[1-9][0-9]* errors?\b'; then
  echo "close-merged: the gate check reported errors; run gh auth status. Nothing closed." >&2
  exit 1
fi

# Beads whose PR was closed unmerged: the check reports their gates as escalated.
for gate in $(printf '%s\n' "$out" | sed -n 's/^.*[[:space:]]\([A-Za-z0-9._-]*\): escalated.*$/\1/p'); do
  for b in $(bd --readonly dep list "$gate" --direction=up --json 2>/dev/null | jq -r '.[].id'); do
    bd label remove "$b" pr-open >/dev/null 2>&1
    bd label add "$b" pr-closed >/dev/null && echo "flagged $b: a PR was closed without merging"
  done
done

gates() {  # one line per gh:pr gate: status <TAB> close reason <TAB> PR URL
  bd --readonly show "$1" --json |
    jq -r '(.[0] // .) | [.dependencies[]? | select(.await_type == "gh:pr")] | .[] | "\(.status)\t\(.close_reason // "")\t\(.await_id)"'
}

while :; do
  closed=0
  for b in $(bd --readonly list -l pr-open --json | jq -r '.[].id'); do
    g=$(gates "$b")
    [ -n "$g" ] || continue
    printf '%s\n' "$g" | awk -F'\t' '$1 != "closed" || $2 !~ /was merged/' | grep -q . && continue  # still in review
    urls=$(printf '%s\n' "$g" | cut -f3 | tr '\n' ' ')
    if bd close "$b" --reason "merged: ${urls% }" >/dev/null 2>&1; then
      bd label remove "$b" pr-open >/dev/null 2>&1
      echo "closed $b"
      closed=$((closed + 1))
    fi
  done
  [ "$closed" -gt 0 ] || break
done
