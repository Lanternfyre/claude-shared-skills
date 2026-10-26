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
#   cap        work awaiting review reached custom.beadwork-review-cap (default 12)
#   delivery   BEADWORK_DELIVERY is not pr, stack or local
#   engine     BEADWORK_ENGINE is not claude or codex
#   verify     the project has no verify command (custom.beadwork-verify): no nights at all
#   card       no role, no role card, the card says night: no, or its effort is not a level
#   nothing    no night-ok bead for the role, ready or blocked (blocked ones may be own-stack)
#   limit      a session hit the usage limit
#   failures   two sessions in a row failed
#   timeout    a hard timeout needs checkout/delegate reconciliation (timebox default 2h)
#   timebox    BEADWORK_BEAD_TIMEBOX is not a whole number with s, m, h or d
# Each session gets BEADWORK_PARK_BY (UTC, YYYY-MM-DDTHH:MMZ), a quarter of the time box before
# it ends: from then on it parks its bead before starting Finish, so the time box rarely kills it.
# Away mode does not stop nights (operator ruling, 2026-10-25).
#
# For tests, these override the live values: BEADWORK_NOW (HH:MM), BEADWORK_REVIEW_CAP,
# BEADWORK_VERIFY, BEADWORK_ROLE_CARD (path).
set -u
here=$(cd "$(dirname "$0")" && pwd)
plugin_root=$(cd "$here/.." && pwd)
dry=no; [ "${1:-}" = "--dry-run" ] && dry=yes

tz=${BEADWORK_TZ:-Europe/Warsaw}
day=${BEADWORK_DAY:-08-23}
cutoff=${BEADWORK_NIGHT_CUTOFF:-06:00}
timebox=${BEADWORK_BEAD_TIMEBOX:-2h}
role=${BEADWORK_ROLE:-}
delivery=${BEADWORK_DELIVERY:-pr}
engine=${BEADWORK_ENGINE:-claude}
default_branch() { git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || echo origin/main; }
role_card_path() {
  if [ -n "${BEADWORK_ROLE_CARD:-}" ]; then echo "$BEADWORK_ROLE_CARD"
  elif [ -n "${BEADWORK_ROLE_DIR:-}" ]; then echo "$BEADWORK_ROLE_DIR/$role.md"
  elif [ -f ".beads/roles/$role.md" ]; then echo ".beads/roles/$role.md"
  else echo ".claude/roles/$role.md"; fi
}
approved_card_path() {
  local base; base=$(default_branch)
  if git cat-file -e "$base:.beads/roles/$role.md" 2>/dev/null; then echo ".beads/roles/$role.md"
  elif git cat-file -e "$base:.claude/roles/$role.md" 2>/dev/null; then echo ".claude/roles/$role.md"; fi
}
card=$(role_card_path)
date_tag=$(TZ=$tz date +%F)
log_dir=${BEADWORK_STATE_DIR:-$HOME/.local/state/beadwork}; mkdir -p "$log_dir"
log="$log_dir/night-$date_tag-${role:-norole}.log"

say() { printf '%s %s\n' "$(TZ=$tz date +%H:%M:%S)" "$*" | tee -a "$log"; }
cfg() {  # a bd config value, or empty when unset
  local v; v=$(bd --readonly config get "$1" 2>/dev/null | tail -1)
  case "$v" in *"(not set"*|"") echo "" ;; *) echo "$v" ;; esac
}
minutes() { local h=${1%:*} m=${1#*:}; echo $(( 10#$h * 60 + 10#$m )); }
count() { local n; n=$("$@" 2>/dev/null); [[ "$n" =~ ^[0-9]+$ ]] && echo "$n" || echo 0; }
seconds() { case $1 in *d) echo $(( ${1%d} * 86400 )) ;; *h) echo $(( ${1%h} * 3600 )) ;; *m) echo $(( ${1%m} * 60 )) ;; *) echo $(( ${1%s} )) ;; esac; }
park_by() { date -u -d "@$(( $(date +%s) + $(seconds "$timebox") * 3 / 4 ))" +%FT%H:%MZ 2>/dev/null; }

# The card as the default branch has it: a session must not change its own model or night
# permission by editing the file. check() rejects automatic path changes away from
# an existing approved card; operator path overrides retain their explicit semantics.
reviewed_card() {
  [ -n "${BEADWORK_ROLE_CARD:-}" ] && { echo "$card"; return; }
  local base out repo policy_path=$card
  base=$(default_branch)
  repo=$(git rev-parse --show-toplevel 2>/dev/null)
  # git show needs a path relative to the repo, including for an absolute ROLE_DIR.
  if [ -n "$repo" ]; then
    case "$card" in "$repo"/*) policy_path=${card#"$repo"/} ;; esac
  fi
  out="$log_dir/card-${role:-norole}.md"
  if git show "$base:$policy_path" > "$out" 2>/dev/null; then echo "$out"; else echo "$card"; fi
}

# Each check prints "go" or "stop <rule>: <reason>".
check() {
  local now night_start n cap pr verify model effort night eligible model_key effort_key
  case "$engine" in
    claude) model_key=model; effort_key=effort ;;
    codex) model_key=codex_model; effort_key=codex_effort ;;
    *) echo "stop engine: BEADWORK_ENGINE=$engine; use claude or codex"; return ;;
  esac
  case "$delivery" in pr|stack|local) ;;
    *) echo "stop delivery: BEADWORK_DELIVERY=$delivery; use pr, stack or local"; return ;; esac
  now=${BEADWORK_NOW:-$(TZ=$tz date +%H:%M)}
  night_start="${day#*-}:00"
  n=$(minutes "$now")
  if [ "$n" -ge "$(minutes "$cutoff")" ] && [ "$n" -lt "$(minutes "$night_start")" ]; then
    echo "stop cutoff: it is $now; no new bead from $cutoff until $night_start"; return; fi

  [[ "$timebox" =~ ^[0-9]+[smhd]?$ ]] || { echo "stop timebox: BEADWORK_BEAD_TIMEBOX=$timebox; use a whole number with s, m, h or d"; return; }
  [ -n "$(park_by)" ] || { echo "stop timebox: cannot compute a park-by time (needs GNU date)"; return; }

  [ -n "$role" ] || { echo "stop card: no BEADWORK_ROLE; nights need a role with a card"; return; }
  card=$(role_card_path)
  local c approved
  if [ -z "${BEADWORK_ROLE_CARD:-}" ] && [ -z "${BEADWORK_ROLE_DIR:-}" ]; then
    approved=$(approved_card_path)
    if [ -n "$approved" ] && [ "$card" != "$approved" ]; then
      echo "stop card: unreviewed role card at $card would replace approved $approved; review the move on the default branch before unattended work"
      return
    fi
  fi
  c=$(reviewed_card)
  night=$("$here/role-card.sh" "$c" night 2>/dev/null) || { echo "stop card: no readable role card at $card"; return; }
  [ "$night" = yes ] || { echo "stop card: $card says night: $night"; return; }
  model=$("$here/role-card.sh" "$c" "$model_key" 2>/dev/null) || { echo "stop card: $card has no $model_key"; return; }
  effort=$("$here/role-card.sh" "$c" "$effort_key" 2>/dev/null | tr '[:upper:]' '[:lower:]')  # empty: engine default
  if [ "$engine" = codex ]; then
    case "$model" in opus|sonnet|haiku|opusplan|claude-*)
      echo "stop card: $card has a Claude model in codex_model; use a Codex model id"; return ;; esac
    case "$effort" in ""|low|medium|high|xhigh) ;;
      *) echo "stop card: $card has codex_effort: $effort; use low, medium, high or xhigh"; return ;; esac
  else
    case "$effort" in ""|low|medium|high|xhigh|max) ;;
      *) echo "stop card: $card has effort: $effort; use low, medium, high, xhigh or max"; return ;; esac
    if [ -n "$effort" ] && ! claude --help 2>/dev/null | grep -q -- '--effort'; then
      echo "stop card: $card sets effort, but this claude has no --effort; update claude"; return; fi
  fi

  verify=${BEADWORK_VERIFY-$(cfg custom.beadwork-verify)}
  [ -n "$verify" ] || { echo "stop verify: no verify command (bd config set custom.beadwork-verify \"<command>\")"; return; }

  cap=${BEADWORK_REVIEW_CAP:-$(cfg custom.beadwork-review-cap)}; cap=${cap:-12}
  local review_label=pr-open
  [ "$delivery" != local ] || review_label=integration-pending
  pr=$(bd --readonly count -l "$review_label" 2>/dev/null || echo "?")
  [[ "$pr" =~ ^[0-9]+$ ]] || { echo "stop cap: cannot count work in review (bd unreachable)"; return; }
  [[ "$cap" =~ ^[0-9]+$ ]] || { echo "stop cap: review cap must be a non-negative integer"; return; }
  [ "$pr" -lt "$cap" ] || { echo "stop cap: $pr items in review, cap $cap"; return; }

  local ready blocked
  ready=$(count sh -c "bd --readonly ready --label 'role:$role' --label night-ok --exclude-type epic,decision --exclude-label human,pr-open,pr-closed --json | jq length")
  blocked=0
  if [ "$delivery" != local ]; then
    # PR mode may maintain its existing review branches; stack mode may also build
    # on its own verified predecessors. The session checks actual ownership/eligibility.
    blocked=$(count sh -c "bd --readonly blocked --json | jq --arg r 'role:$role' --arg mode '$delivery' '[.[] | select((.labels // []) | (index(\$r) and index(\"night-ok\") and (index(\"human\") | not) and (index(\"pr-closed\") | not))) | select(.issue_type != \"epic\" and .issue_type != \"decision\") | select(\$mode == \"stack\" or ((.labels // []) | index(\"pr-open\")))] | length'")
  fi
  eligible=$(( ready + blocked ))
  [ "$eligible" -gt 0 ] || { echo "stop nothing: no night-ok bead for role $role"; return; }

  echo "go model=$model effort=${effort:-default} park-by=$(park_by) eligible=$eligible review=$pr/$cap delivery=$delivery engine=$engine"
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
    echo; echo "Sessions (outcome, bead, PR or commit):"
    if [ "${#session_results[@]}" -gt 0 ]; then
      printf '%s\n' "${session_results[@]}" | sed 's/^BEADWORK-NIGHT: /- /'
    else echo "- none"; fi
    echo; echo "Log: $log"
  } > "$body"
  bd create -t chore -l "human,morning-summary${role:+,role:$role}" --title "Night summary $date_tag ${role:-norole}" \
     --body-file "$body" --validate --silent >/dev/null && say "summary bead filed"
  rm -f "$body"
}

record_result() { session_results+=("$1"); say "$1"; }

if [ "$dry" = yes ]; then check; exit 0; fi
if [ "${1:-}" = "--install-guard" ]; then guard_pushes; exit 0; fi

guard_pushes
say "night starts (engine $engine, role $role, card $card, time box $timebox)"
session_results=()
failures=0; reason=""
while :; do
  case "$delivery" in
    pr|stack)
      if ! sweep=$("$here/close-merged.sh" 2>&1); then
        say "$sweep"
        say "merge state unavailable; the session may only claim independently ready work, excluding review beads"
      else say "$sweep"; fi ;;
  esac
  verdict=$(check); say "$verdict"
  case "$verdict" in stop*) reason=${verdict#stop }; break ;; esac
  model=$(printf '%s' "$verdict" | sed -n 's/.*model=\([^ ]*\).*/\1/p')
  effort=$(printf '%s' "$verdict" | sed -n 's/.*effort=\([^ ]*\).*/\1/p')
  out=$(mktemp)
  result=$out
  park=$(park_by); say "session starts; park by $park"
  if [ "$engine" = codex ]; then
    result=$(mktemp)
    args=(exec --model "$model")
    [ "$effort" = default ] || args+=(-c "model_reasoning_effort=\"$effort\"")
    args+=(--sandbox workspace-write --output-last-message "$result")
    prompt="Read and follow the exact skill at $plugin_root/skills/slice/SKILL.md and its referenced files. Run that skill in night mode (arguments: night), handling one bead and then exiting. If this plugin's SessionStart context is absent, run $plugin_root/hooks/session-start.sh and read its output before beginning. Respect plugin trust, normal approvals and the workspace sandbox; if required approval is unavailable, report the blocker rather than bypassing it. Put exactly one BEADWORK-NIGHT result line in your final response."
    BEADWORK_PARK_BY=$park BEADWORK_PLUGIN_ROOT=$plugin_root timeout "$timebox" codex "${args[@]}" "$prompt" > "$out" 2>&1
  else
    args=(--model "$model"); [ "$effort" = default ] || args+=(--effort "$effort")
    BEADWORK_PARK_BY=$park CLAUDE_CODE_SYNC_PLUGIN_INSTALL=1 timeout "$timebox" claude -p "/beadwork:slice night" "${args[@]}" > "$out" 2>&1
  fi
  rc=$?
  cat "$out" >> "$log"
  if [ "$engine" = codex ]; then
    cat "$result" >> "$log"
    status=$(grep -E '^BEADWORK-NIGHT: (pr|fixed|complete|review|parked|blocked|nothing) [^[:space:]]+ [^[:space:]]+[[:space:]]*$' "$result" | tail -1)
  else
    status=$(grep -o 'BEADWORK-NIGHT: .*' "$result" | tail -1)
  fi
  if grep -qi 'usage limit' "$out" "$result"; then reason="limit: the usage limit was hit"; rm -f "$out" "$result"; break; fi
  rm -f "$out" "$result"
  if [ "$rc" -eq 124 ]; then
    record_result "BEADWORK-NIGHT: timeout - - (the time box of $timebox ran out)"
    # The model session has not reliably reported its exact claim. An actor may own
    # concurrent sessions; choosing its first in-progress bead can release live work.
    # Leave ownership to lease expiry/reconciliation rather than guessing an id.
    say "claim not released: inspect this session's log and checkout; notes may predate its work. Confirm delegates stopped before recovery."
    reason="timeout: reconcile delegates, ownership and checkout before another session"
    break
  elif [ "$rc" -ne 0 ] || [ -z "$status" ]; then
    record_result "BEADWORK-NIGHT: failed - - (exit $rc, no status line)"; failures=$((failures + 1))
  else
    record_result "$status"
    case "$status" in *" nothing "*|*"BEADWORK-NIGHT: nothing"*) reason="nothing: the session found no claimable night-ok bead"; break ;; esac
    failures=0
  fi
  [ "$failures" -lt 2 ] || { reason="failures: two sessions in a row failed"; break; }
done
say "night ends: $reason"
summary "$reason"
