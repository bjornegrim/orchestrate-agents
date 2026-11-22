#!/bin/sh
# Usage: sh snapshot.sh <path>...
# Prints the git tree id of HEAD plus the working-tree state of the named paths.
# The real index is never touched.
set -eu
[ "$#" -gt 0 ] || { echo "usage: snapshot.sh <path>..." >&2; exit 2; }

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
export GIT_INDEX_FILE="$tmp/index"

if git rev-parse --verify -q HEAD >/dev/null; then git read-tree HEAD; else git read-tree --empty; fi
git add -A -- "$@"
git write-tree
