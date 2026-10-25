#!/usr/bin/env bash
# Print one header field of a role card.
#
#   role-card.sh <card.md> <field>        e.g. role-card.sh .claude/roles/maintainer.md model
#
# The header is the flat `key: value` block between the card's first two `---` lines.
# Exits 2 when the card is missing, 1 when the field is absent or empty.
set -u
card=${1:?usage: role-card.sh <card.md> <field>}
field=${2:?usage: role-card.sh <card.md> <field>}
[ -r "$card" ] || { echo "role-card: no role card at $card" >&2; exit 2; }

value=$(awk 'NR == 1 && $0 == "---" { h = 1; next } h && $0 == "---" { exit } h' "$card" |
        sed -n "s/^${field}:[[:space:]]*//p" | head -1 | sed 's/[[:space:]]*$//')
[ -n "$value" ] || { echo "role-card: no '$field' in $card" >&2; exit 1; }
printf '%s\n' "$value"
