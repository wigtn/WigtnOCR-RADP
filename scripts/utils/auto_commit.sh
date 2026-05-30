#!/bin/bash
# Usage: auto_commit.sh "commit message" file1 [file2 ...]
# Adds and commits files if they exist + differ; no-op if no changes.
set -e
cd /mnt/data1/work/WigtnOCR-RADP
MSG="$1"
shift
for f in "$@"; do
  if [ -e "$f" ]; then
    git add "$f"
  fi
done
if git diff --cached --quiet; then
  echo "auto_commit: nothing to commit"
  exit 0
fi
git commit -m "$MSG

Auto-commit by k16 pipeline auto_commit.sh.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
echo "auto_commit: committed → $(git log -1 --oneline)"
