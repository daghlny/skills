#!/usr/bin/env bash
# Stop a TUI application by killing its tmux session.
# Usage: tui_stop.sh <session-name>

set -euo pipefail

SESSION="${1:?Usage: tui_stop.sh <session>}"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    tmux kill-session -t "$SESSION"
    echo "Session '$SESSION' stopped"
else
    echo "Session '$SESSION' not found (already stopped?)"
fi
