#!/usr/bin/env bash
# Check committed changes against a role card's expected and protected paths.
#
#   role-check.sh <card.md> [base-ref] [policy-ref]
# base defaults to the remote's default branch; policy-ref defaults to base-ref.
# For stacks, base-ref is the branch below; policy-ref is the default branch.
#
# `paths:` is advisory; `protected:` blocks even inside expected paths. Exits 1 for
# protected changes, 0 otherwise, 2 on missing policy/base or an unreadable diff.
# Globs `*` and `**` both match across folders. This checks paths, not the card's prose.
set -u
here=$(cd "$(dirname "$0")" && pwd)
card=${1:?usage: role-check.sh <card.md> [base-ref] [policy-ref]}
base=${2:-$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)}
policy=${3:-$base}
repo=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "role-check: not in a Git repository" >&2; exit 2; }
case "$card" in
  "$repo"/*) card=${card#"$repo"/} ;;
  /*) echo "role-check: $card is outside the repository; record explicit authorization rather than using it as approved repository policy" >&2; exit 2 ;;
  ./*) card=${card#./} ;;
esac
fork=$(git merge-base HEAD "$base" 2>/dev/null) || { echo "role-check: cannot find base $base" >&2; exit 2; }
git rev-parse --verify "$policy^{commit}" >/dev/null 2>&1 || { echo "role-check: cannot find policy ref $policy" >&2; exit 2; }

# Read approved policy separately from the diff base, so a lower stack branch cannot
# relax protections for the branch above. A new card needs review before it is policy.
scratch=$(mktemp -d) || exit 2
trap 'rm -rf "$scratch"' EXIT
reviewed="$scratch/card"
if ! git show "$policy:$card" > "$reviewed" 2>/dev/null; then
  echo "role-check: no approved card at $policy:$card; review the new card before using it as policy" >&2
  exit 2
fi
paths=$("$here/role-card.sh" "$reviewed" paths) || exit 2
protected=$("$here/role-card.sh" "$reviewed" protected 2>/dev/null) || protected=""

IFS=',' read -r -a globs <<< "$paths"
IFS=',' read -r -a guards <<< "$protected"
matches() {
  local file=$1 g
  shift
  for g in "$@"; do
    g=$(printf '%s' "$g" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
    [ -n "$g" ] || continue
    # shellcheck disable=SC2053  # unquoted on purpose: $g is a pattern
    [[ $file == $g ]] && return 0
  done
  return 1
}

# --no-renames checks both ends of moves, including a deletion from a protected path.
git diff --name-only --no-renames -z "$fork" HEAD > "$scratch/files" || exit 2
blocked=0
while IFS= read -r -d '' file; do
  if matches "$file" "${guards[@]}"; then
    printf 'protected path (requires explicit authorization): %s\n' "$file"
    blocked=1
  elif ! matches "$file" "${globs[@]}"; then
    printf 'outside expected scope (explain and verify): %s\n' "$file"
  fi
done < "$scratch/files"

exit "$blocked"
