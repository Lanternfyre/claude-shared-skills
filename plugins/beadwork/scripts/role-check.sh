#!/usr/bin/env bash
# Check the current branch's changed files against a role card's allowed paths.
#
#   role-check.sh <card.md> [base-ref]      base defaults to the remote's default branch
#
# Lists every changed file (committed on this branch since it left the base) that no glob in
# the card's `paths:` matches, and exits 1 if there are any; exits 0 when all fit. A glob's
# `*` and `**` both match across folders. Exits 2 on a missing card or base.
set -u
here=$(cd "$(dirname "$0")" && pwd)
card=${1:?usage: role-check.sh <card.md> [base-ref]}
base=${2:-$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)}
fork=$(git merge-base HEAD "$base" 2>/dev/null) || { echo "role-check: cannot find base $base" >&2; exit 2; }

# Read the card as the base branch has it: a branch must not widen its own fence by
# editing its card. Only a repo whose base has no card yet falls back to the working copy.
reviewed=$(mktemp); trap 'rm -f "$reviewed"' EXIT
if git show "$fork:$card" > "$reviewed" 2>/dev/null; then
  paths=$("$here/role-card.sh" "$reviewed" paths) || exit 2
else
  echo "role-check: $card is not on $base yet; using the working copy" >&2
  paths=$("$here/role-card.sh" "$card" paths) || exit 2
fi

IFS=',' read -r -a globs <<< "$paths"
outside=0
while IFS= read -r file; do
  [ -n "$file" ] || continue
  fits=no
  for g in "${globs[@]}"; do
    g=$(printf '%s' "$g" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
    # shellcheck disable=SC2053  # unquoted on purpose: $g is a pattern
    [[ $file == $g ]] && { fits=yes; break; }
  done
  if [ "$fits" = no ]; then echo "outside the role's paths: $file"; outside=1; fi
done < <(git diff --name-only "$fork" HEAD)

exit "$outside"
