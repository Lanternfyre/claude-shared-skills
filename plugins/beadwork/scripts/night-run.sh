#!/usr/bin/env bash
# The night loop: one fresh headless session per bead until a stop rule fires, then a
# morning-summary bead. Run inside a box, in the project's checkout (the homelab job does).
#
#   night-run.sh [--dry-run | --install-guard]
#     --dry-run        check every stop rule, print the verdict, start nothing
#     --install-guard  only install the pre-push guard in this checkout
#
# Stop rules, checked before each bead:
#   cutoff     no new bead from BEADWORK_NIGHT_CUTOFF (06:00) until the day ends (BEADWORK_DAY's end)
#   cap        PRs in review (pr-open beads) reached custom.beadwork-review-cap (default 12)
#   verify     the project has no verify command (custom.beadwork-verify): no nights at all
#   card       no role, no role card, the card says night: no, or its effort is not a level
#   nothing    no night-ok bead for the role, ready or blocked (blocked ones may be own-stack)
#   limit      a session hit the usage limit
#   failures   two sessions in a row failed or timed out (BEADWORK_BEAD_TIMEBOX, default 2h)
# Each session gets BEADWORK_PARK_BY (YYYY-MM-DDTHH:MM), a quarter of the time box before it ends: from
# then on it parks its bead at the next milestone, so the time box rarely has to kill it.
# Away mode does not stop nights (operator ruling, 2026-10-25).
#
# For tests, these override the live values: BEADWORK_NOW (HH:MM), BEADWORK_REVIEW_CAP,
# BEADWORK_VERIFY, BEADWORK_ROLE_CARD (path).
set -u
here=$(cd "$(dirname "$0")" && pwd)
dry=no; [ "${1:-}" = "--dry-run" ] && dry=yes

tz=${BEADWORK_TZ:-Europe/Warsaw}
day=${BEADWORK_DAY:-08-23}
cutoff=${BEADWORK_NIGHT_CUTOFF:-06:00}
timebox=${BEADWORK_BEAD_TIMEBOX:-2h}
role=${BEADWORK_ROLE:-}
card=${BEADWORK_ROLE_CARD:-.claude/roles/$role.md}
date_tag=$(TZ=$tz date +%F)
log_dir="$HOME/.local/state/beadwork"; mkdir -p "$log_dir"
log="$log_dir/night-$date_tag-${role:-norole}.log"

say() { printf '%s %s\n' "$(TZ=$tz date +%H:%M:%S)" "$*" | tee -a "$log"; }
cfg() {  # a bd config value, or empty when unset
  local v; v=$(bd --readonly config get "$1" 2>/dev/null | tail -1)
  case "$v" in *"(not set"*|"") echo "" ;; *) echo "$v" ;; esac
}
minutes() { local h=${1%:*} m=${1#*:}; echo $(( 10#$h * 60 + 10#$m )); }
count() { local n; n=$("$@" 2>/dev/null); [[ "$n" =~ ^[0-9]+$ ]] && echo "$n" || echo 0; }
seconds() { case $1 in *d) echo $(( ${1%d} * 86400 )) ;; *h) echo $(( ${1%h} * 3600 )) ;; *m) echo $(( ${1%m} * 60 )) ;; *) echo $(( ${1%s} )) ;; esac; }
park_by() { TZ=$tz date -d "@$(( $(date +%s) + $(seconds "$timebox") * 3 / 4 ))" +%FT%H:%M; }

# The card as the default branch has it: a session must not change its own model or night
# permission by editing the file. Only a card not yet on the default branch is read as is.
reviewed_card() {
  [ -n "${BEADWORK_ROLE_CARD:-}" ] && { echo "$card"; return; }
  local base out; base=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main)
  out="$log_dir/card-${role:-norole}.md"
  if git show "$base:$card" > "$out" 2>/dev/null; then echo "$out"; else echo "$card"; fi
}

# Each check prints "go" or "stop <rule>: <reason>".
check() {
  local now night_start n cap pr verify model effort night eligible
  now=${BEADWORK_NOW:-$(TZ=$tz date +%H:%M)}
  night_start="${day#*-}:00"
  n=$(minutes "$now")
  if [ "$n" -ge "$(minutes "$cutoff")" ] && [ "$n" -lt "$(minutes "$night_start")" ]; then
    echo "stop cutoff: it is $now; no new bead from $cutoff until $night_start"; return; fi

  [ -n "$role" ] || { echo "stop card: no BEADWORK_ROLE; nights need a role with a card"; return; }
  local c; c=$(reviewed_card)
  night=$("$here/role-card.sh" "$c" night 2>/dev/null) || { echo "stop card: no readable role card at $card"; return; }
  [ "$night" = yes ] || { echo "stop card: $card says night: $night"; return; }
  model=$("$here/role-card.sh" "$c" model 2>/dev/null) || { echo "stop card: $card has no model"; return; }
  effort=$("$here/role-card.sh" "$c" effort 2>/dev/null | tr '[:upper:]' '[:lower:]')  # empty: claude's default
  case "$effort" in ""|low|medium|high|xhigh|max) ;;
    *) echo "stop card: $card has effort: $effort; use low, medium, high, xhigh or max"; return ;; esac
  if [ -n "$effort" ] && ! claude --help 2>/dev/null | grep -q -- '--effort'; then
    echo "stop card: $card sets effort, but this claude has no --effort; update claude"; return; fi

  verify=${BEADWORK_VERIFY-$(cfg custom.beadwork-verify)}
  [ -n "$verify" ] || { echo "stop verify: no verify command (bd config set custom.beadwork-verify \"<command>\")"; return; }

  cap=${BEADWORK_REVIEW_CAP:-$(cfg custom.beadwork-review-cap)}; cap=${cap:-12}
  pr=$(bd --readonly count -l pr-open 2>/dev/null || echo "?")
  [ "$pr" != "?" ] || { echo "stop cap: cannot count PRs in review (bd unreachable)"; return; }
  [ "$pr" -lt "$cap" ] || { echo "stop cap: $pr PRs in review, cap $cap"; return; }

  local ready blocked
  ready=$(count sh -c "bd --readonly ready --label 'role:$role' --label night-ok --exclude-type epic,decision --exclude-label human --json | jq length")
  blocked=$(count sh -c "bd --readonly blocked --json | jq --arg r 'role:$role' '[.[] | select((.labels // []) | (index(\$r) and index(\"night-ok\") and (index(\"human\") | not)))] | length'")
  eligible=$(( ready + blocked ))
  [ "$eligible" -gt 0 ] || { echo "stop nothing: no night-ok bead for role $role"; return; }

  echo "go model=$model effort=${effort:-default} park-by=$(park_by) eligible=$eligible prs=$pr/$cap"
}

# Pushes to the default branch and branch deletions are refused in this checkout.
guard_pushes() {
  local hook default
  hook="$(git rev-parse --git-path hooks)/pre-push"
  default=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null | sed 's#^origin/##'); default=${default:-main}
  grep -q 'beadwork night guard' "$hook" 2>/dev/null && return
  [ -e "$hook" ] && { say "pre-push hook exists and is not ours; not replacing it"; return; }
  cat > "$hook" <<EOF
#!/usr/bin/env bash
# beadwork night guard: never push to $default, never delete a remote branch.
while read -r _lref lsha rref _rsha; do
  [ "\$rref" = "refs/heads/$default" ] && { echo "beadwork night guard: no pushes to $default" >&2; exit 1; }
  [ "\$lsha" = "0000000000000000000000000000000000000000" ] && { echo "beadwork night guard: no branch deletions" >&2; exit 1; }
done
exit 0
EOF
  chmod +x "$hook"
}

summary() {
  local reason=$1 body
  body=$(mktemp)
  {
    echo "## Task"; echo "Morning read of the night run ($date_tag, role ${role:-none})."; echo
    echo "## Guardrails"; echo "Read-only."; echo
    echo "## Acceptance Criteria"; echo "The operator has read it; the grill closes it."; echo
    echo "## Summary"
    echo "Stopped: $reason"
    echo; echo "Sessions (outcome, bead, PR):"
    lines=$(grep -o 'BEADWORK-NIGHT: .*' "$log" | sed 's/^BEADWORK-NIGHT: /- /')
    echo "${lines:-- none}"
    echo; echo "Log: $log"
  } > "$body"
  bd create -t chore -l "human,morning-summary${role:+,role:$role}" --title "Night summary $date_tag ${role:-norole}" \
     --body-file "$body" --validate --silent >/dev/null && say "summary bead filed"
  rm -f "$body"
}

if [ "$dry" = yes ]; then check; exit 0; fi
if [ "${1:-}" = "--install-guard" ]; then guard_pushes; exit 0; fi

guard_pushes
say "night starts (role $role, card $card, time box $timebox)"
failures=0; reason=""
while :; do
  if ! sweep=$("$here/close-merged.sh" 2>&1); then say "$sweep"; reason="gh: cannot reach GitHub (close-merged.sh failed)"; break; fi
  say "$sweep"
  verdict=$(check); say "$verdict"
  case "$verdict" in stop*) reason=${verdict#stop }; break ;; esac
  model=$(printf '%s' "$verdict" | sed -n 's/.*model=\([^ ]*\).*/\1/p')
  effort=$(printf '%s' "$verdict" | sed -n 's/.*effort=\([^ ]*\).*/\1/p')
  args=(--model "$model"); [ "$effort" = default ] || args+=(--effort "$effort")
  park=$(printf '%s' "$verdict" | sed -n 's/.*park-by=\([^ ]*\).*/\1/p')
  out=$(mktemp)
  BEADWORK_PARK_BY=$park CLAUDE_CODE_SYNC_PLUGIN_INSTALL=1 timeout "$timebox" claude -p "/beadwork:slice night" "${args[@]}" > "$out" 2>&1
  rc=$?
  cat "$out" >> "$log"
  status=$(grep -o 'BEADWORK-NIGHT: .*' "$out" | tail -1)
  if grep -qi 'usage limit' "$out"; then reason="limit: the usage limit was hit"; rm -f "$out"; break; fi
  rm -f "$out"
  if [ "$rc" -eq 124 ]; then
    say "BEADWORK-NIGHT: timeout - - (the time box of $timebox ran out)"
    bead=$(bd --readonly list --status in_progress --assignee "${BEADS_ACTOR:-}" --json 2>/dev/null | jq -r '.[0].id // empty')
    if [ -n "$bead" ]; then
      bd comments add "$bead" "Night loop: the $timebox time box ran out mid-session. The notes may be older than the work on the branch." >/dev/null
      bd unclaim "$bead" --reason "night time box ($timebox) ran out" >/dev/null && say "parked $bead"
    fi
    failures=$((failures + 1))
  elif [ "$rc" -ne 0 ] || [ -z "$status" ]; then
    say "BEADWORK-NIGHT: failed - - (exit $rc, no status line)"; failures=$((failures + 1))
  else
    say "$status"
    case "$status" in *" nothing "*|*"BEADWORK-NIGHT: nothing"*) reason="nothing: the session found no claimable night-ok bead"; break ;; esac
    failures=0
  fi
  [ "$failures" -lt 2 ] || { reason="failures: two sessions in a row failed"; break; }
done
say "night ends: $reason"
summary "$reason"
