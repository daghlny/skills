#!/usr/bin/env bash
# Install skills from this repo to one or more agent skill directories.
#
# Remote one-liner:
#   curl -fsSL https://raw.githubusercontent.com/Daghlny/skills/main/install.sh | bash
#
# Or clone and run locally:
#   git clone https://github.com/Daghlny/skills.git && cd skills && ./install.sh
#
# Env vars:
#   INSTALL_TARGETS=claude,codex,agent   Skip the interactive prompt and install
#                                        to the given targets (comma-separated).
#                                        Use "all" to install to every detected target.

set -euo pipefail

# Candidate targets: label -> destination directory
CANDIDATES=(
  "claude:$HOME/.claude/skills"
  "codex:$HOME/.codex/skills"
  "agent:$HOME/.agent/skills"
)

# Detect which target *parent* dirs already exist (e.g. ~/.claude, ~/.codex).
AVAILABLE_LABELS=()
AVAILABLE_DESTS=()
for entry in "${CANDIDATES[@]}"; do
  label="${entry%%:*}"
  dest="${entry#*:}"
  parent="$(dirname "$dest")"
  if [ -d "$parent" ]; then
    AVAILABLE_LABELS+=("$label")
    AVAILABLE_DESTS+=("$dest")
  fi
done

if [ "${#AVAILABLE_LABELS[@]}" -eq 0 ]; then
  echo "Error: none of ~/.claude, ~/.codex, ~/.agent exist."
  echo "Create at least one of them (or install the corresponding agent) first."
  exit 1
fi

# Decide which targets to install to.
SELECTED_DESTS=()

select_by_labels() {
  # $1 = comma-separated labels (or "all")
  local raw="$1"
  if [ "$raw" = "all" ]; then
    SELECTED_DESTS=("${AVAILABLE_DESTS[@]}")
    return
  fi
  local IFS=','
  for want in $raw; do
    want="$(echo "$want" | tr -d '[:space:]')"
    [ -z "$want" ] && continue
    local found=0
    for i in "${!AVAILABLE_LABELS[@]}"; do
      if [ "${AVAILABLE_LABELS[$i]}" = "$want" ]; then
        SELECTED_DESTS+=("${AVAILABLE_DESTS[$i]}")
        found=1
        break
      fi
    done
    if [ "$found" -eq 0 ]; then
      echo "Warning: target '$want' is not available (parent dir missing), skipping."
    fi
  done
}

if [ -n "${INSTALL_TARGETS:-}" ]; then
  select_by_labels "$INSTALL_TARGETS"
else
  # Interactive prompt. Read from /dev/tty so this works under `curl | bash`.
  if [ -r /dev/tty ]; then
    {
      echo "Detected available targets:"
      for i in "${!AVAILABLE_LABELS[@]}"; do
        printf "  %d) %s  ->  %s\n" "$((i + 1))" "${AVAILABLE_LABELS[$i]}" "${AVAILABLE_DESTS[$i]}"
      done
      echo "  a) all of the above"
      echo ""
      printf "Install to which? [comma-separated numbers, labels, or 'a'] (default: a): "
    } >&2
    read -r choice < /dev/tty || choice=""
    choice="$(echo "$choice" | tr -d '[:space:]')"
    if [ -z "$choice" ] || [ "$choice" = "a" ] || [ "$choice" = "all" ]; then
      SELECTED_DESTS=("${AVAILABLE_DESTS[@]}")
    else
      IFS=',' read -ra parts <<< "$choice"
      for p in "${parts[@]}"; do
        if [[ "$p" =~ ^[0-9]+$ ]]; then
          idx=$((p - 1))
          if [ "$idx" -ge 0 ] && [ "$idx" -lt "${#AVAILABLE_DESTS[@]}" ]; then
            SELECTED_DESTS+=("${AVAILABLE_DESTS[$idx]}")
          else
            echo "Warning: index '$p' out of range, skipping."
          fi
        else
          select_by_labels "$p"
        fi
      done
    fi
  else
    echo "No TTY available; defaulting to all detected targets."
    SELECTED_DESTS=("${AVAILABLE_DESTS[@]}")
  fi
fi

if [ "${#SELECTED_DESTS[@]}" -eq 0 ]; then
  echo "Nothing selected. Aborting."
  exit 1
fi

# Determine repo root: if running from a cloned repo, use local files;
# otherwise, clone to a temp directory first.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"
if [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR/skills" ]; then
  REPO_DIR="$SCRIPT_DIR"
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

install_to() {
  local dest="$1"
  echo ""
  echo "==> Installing to $dest"
  mkdir -p "$dest"
  local count=0
  for entry in "$SKILLS_SRC"/*/; do
    [ -d "$entry" ] || continue
    local name
    name="$(basename "$entry")"

    if [ -L "$dest/$name" ]; then
      echo "  Skipped (symlink exists): $name"
      continue
    fi

    if [ -d "$dest/$name" ]; then
      echo "  Updating: $name"
    else
      echo "  Installing: $name"
    fi

    mkdir -p "$dest/$name"
    cp -R "$entry"* "$dest/$name/"
    count=$((count + 1))
  done
  echo "  ($count skill(s) written)"
}

for dest in "${SELECTED_DESTS[@]}"; do
  install_to "$dest"
done

echo ""
echo "Done! Restart your agent or start a new session to use the skills."
