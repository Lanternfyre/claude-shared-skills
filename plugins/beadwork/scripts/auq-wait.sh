#!/usr/bin/env bash
# Wait for auq answers, surviving the server's rate limit.
#
#   auq-wait.sh <id,id,...> [max-secs, default 1800]
#
# Prints the answers JSON and exits 0 once every question is answered. Exits 3 when
# max-secs pass with questions still open: they stay live in auq; wait again, never
# re-post. A 429 from the server (it happens while another session polls) is waited out
# and retried with the same ids; plain `auq await` exits 1 on it.
set -u
ids=${1:?usage: auq-wait.sh <id,id,...> [max-secs]}
max=${2:-1800}
end=$(( $(date +%s) + max ))

while :; do
  left=$(( end - $(date +%s) ))
  if [ "$left" -le 0 ]; then
    echo "auq-wait: still pending after ${max}s; the questions stay live, wait on the same ids" >&2
    exit 3
  fi
  out=$(auq await "$ids" --max-secs "$left" 2>&1)
  rc=$?
  if [ "$rc" -eq 0 ]; then printf '%s\n' "$out"; exit 0; fi
  if [ "$rc" -eq 3 ]; then continue; fi                               # auq's own cap: re-check ours
  if printf '%s' "$out" | grep -q '429'; then sleep 30; continue; fi  # rate limited: same ids, later
  printf '%s\n' "$out" >&2
  exit "$rc"
done
