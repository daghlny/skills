#!/usr/bin/env bash
# Install skills from this repo to ~/.claude/skills.
#
# Remote one-liner:
#   curl -fsSL https://raw.githubusercontent.com/Daghlny/skills/main/install.sh | bash
#
# Or clone and run locally:
#   git clone https://github.com/Daghlny/skills.git && cd skills && ./install.sh

set -euo pipefail

SKILLS_DEST="$HOME/.claude/skills"

# Determine repo root: if running from a cloned repo, use local files;
# otherwise, clone to a temp directory first.
if [ -d "$(dirname "$0")/skills" ]; then
  REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
else
  REPO_DIR="$(mktemp -d)"
  echo "Cloning skills repo..."
  git clone --depth 1 https://github.com/Daghlny/skills.git "$REPO_DIR"
fi

SKILLS_SRC="$REPO_DIR/skills"

if [ ! -d "$SKILLS_SRC" ]; then
  echo "Error: skills directory not found at $SKILLS_SRC"
  exit 1
fi

mkdir -p "$SKILLS_DEST"

installed=0
for entry in "$SKILLS_SRC"/*/; do
  [ -d "$entry" ] || continue
  name="$(basename "$entry")"

  if [ -d "$SKILLS_DEST/$name" ]; then
    echo "Updating: $name"
  else
    echo "Installing: $name"
  fi

  # Don't overwrite if target is a symlink (user might have a system skill there)
  if [ -L "$SKILLS_DEST/$name" ]; then
    echo "  Skipped (symlink exists)"
    continue
  fi

  mkdir -p "$SKILLS_DEST/$name"
  cp -R "$entry"* "$SKILLS_DEST/$name/"
  installed=$((installed + 1))
done

echo ""
echo "Done! Installed $installed skill(s) to $SKILLS_DEST"
echo "Restart Claude Code or start a new session to use the skills."
