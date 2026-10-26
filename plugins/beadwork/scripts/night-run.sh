#!/usr/bin/env bash
# Compatibility schedule: the shared worker loop owns sessions, leases and recovery.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
exec python3 "$here/run.py" --engine "${BEADWORK_ENGINE:-claude}" \
  --mode unattended --label night-ok --legacy-night-schedule \
  --time-budget "${BEADWORK_BEAD_TIMEBOX:-2h}" "$@"
