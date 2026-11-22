#!/bin/sh
# Usage: sh served-model.sh <agent-id> [projects-dir]
# Prints the models that answered in a subagent's log, one per line.
# A log also records the requested model, so match the message object only.
set -eu
id=${1:-}
case "$id" in
  '' | *[!A-Za-z0-9_-]*) echo "usage: served-model.sh <agent-id> [projects-dir]" >&2; exit 2 ;;
esac
root=${2:-"$HOME/.claude/projects"}

models=$(
  grep -ho '"message":{"model":"[^"]*"' "$root"/*/*/subagents/agent-"$id".jsonl 2>/dev/null |
    cut -d '"' -f 6 | LC_ALL=C sort -u
) || true
[ -n "$models" ] || { echo "no answering model found for agent $id" >&2; exit 3; }
printf '%s\n' "$models"
