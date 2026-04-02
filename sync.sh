#!/usr/bin/env bash
# Sync skills from ~/.claude/skills to this repo.
# Only copies user-created skill directories (skips symlinks).

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_SRC="$HOME/.claude/skills"
SKILLS_DEST="$REPO_DIR/skills"

if [ ! -d "$SKILLS_SRC" ]; then
  echo "Error: $SKILLS_SRC does not exist"
  exit 1
fi

synced=0
for entry in "$SKILLS_SRC"/*/; do
  [ -d "$entry" ] || continue
  # Skip symlinks (these are system/built-in skills)
  [ -L "${entry%/}" ] && continue

  name="$(basename "$entry")"
  echo "Syncing: $name"
  mkdir -p "$SKILLS_DEST/$name"
  rsync -a --delete "$entry" "$SKILLS_DEST/$name/"
  synced=$((synced + 1))
done

echo "Done. Synced $synced skill(s) to $SKILLS_DEST"
