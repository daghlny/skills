#!/usr/bin/env bash
# Send a keystroke to a TUI application running in tmux.
# Usage: tui_send.sh <session-name> <key> [delay_ms]

set -euo pipefail

SESSION="${1:?Usage: tui_send.sh <session> <key> [delay_ms]}"
KEY="${2:?Usage: tui_send.sh <session> <key> [delay_ms]}"
DELAY_MS="${3:-500}"

# Verify session exists
if ! tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Error: tmux session '$SESSION' not found" >&2
    exit 1
fi

# Send the key
tmux send-keys -t "$SESSION" "$KEY"

# Wait for the app to process the input
if [ "$DELAY_MS" -gt 0 ]; then
    sleep "$(echo "scale=3; $DELAY_MS / 1000" | bc)"
fi

echo "Sent '$KEY' to session '$SESSION'"
