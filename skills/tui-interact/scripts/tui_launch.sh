#!/usr/bin/env bash
# Launch a TUI application inside a tmux session.
# Usage: tui_launch.sh <session-name> <command> [width] [height]
#
# If width/height are omitted, attempts to detect a reasonable size:
#   1. Checks for an active non-tmux terminal's size via `stty`
#   2. Reads $COLUMNS/$LINES if set
#   3. Falls back to 120x40

set -euo pipefail

SESSION="${1:?Usage: tui_launch.sh <session> <command> [width] [height]}"
COMMAND="${2:?Usage: tui_launch.sh <session> <command> [width] [height]}"

# Auto-detect terminal size if not specified
if [ -z "${3:-}" ]; then
    # Try to get size from the user's actual terminal (largest open one)
    # On macOS, check if there's a Terminal.app or iTerm2 window we can query
    DETECTED_W=""
    DETECTED_H=""

    # Method 1: Check if any real terminal has a known size via /dev/tty
    if [ -e /dev/tty ]; then
        DETECTED=$(stty size < /dev/tty 2>/dev/null || true)
        if [ -n "$DETECTED" ]; then
            DETECTED_H=$(echo "$DETECTED" | awk '{print $1}')
            DETECTED_W=$(echo "$DETECTED" | awk '{print $2}')
        fi
    fi

    # Method 2: Fall back to environment variables
    if [ -z "$DETECTED_W" ] || [ "$DETECTED_W" -lt 40 ] 2>/dev/null; then
        DETECTED_W="${COLUMNS:-120}"
        DETECTED_H="${LINES:-40}"
    fi

    WIDTH="$DETECTED_W"
    HEIGHT="$DETECTED_H"
else
    WIDTH="$3"
    HEIGHT="${4:-40}"
fi

# Kill existing session if any
tmux kill-session -t "$SESSION" 2>/dev/null || true

# Create new detached session with specified dimensions
tmux new-session -d -s "$SESSION" -x "$WIDTH" -y "$HEIGHT" "$COMMAND"

# Wait a moment for the app to initialize
sleep 1

echo "Session '$SESSION' started (${WIDTH}x${HEIGHT}), running: $COMMAND"
