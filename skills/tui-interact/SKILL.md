---
name: tui-interact
description: >
  Provides eyes and hands for interacting with TUI (Terminal UI) applications.
  Use this skill whenever you need to launch, operate, observe, or test a terminal-based
  application — including games built with BubbleTea, tview, termbox, crossterm, curses, etc.
  This skill should be used when the user asks you to run a TUI app, playtest a terminal game,
  check UI rendering, debug TUI layout issues, or perform any task that requires seeing and
  interacting with a full-screen terminal application. Even if the user just says "run it and
  see what it looks like" or "play the game and find bugs", use this skill — it gives you the
  ability to see terminal UI output and send keystrokes, which you cannot do with plain Bash.
---

# TUI Interact

This skill gives you the ability to **see** and **operate** any TUI (Terminal UI) application by running it inside a `tmux` session. Think of it as remote-controlling a terminal: you can launch an app, send keystrokes, and capture what's on screen — either as plain text or as a rendered PNG screenshot.

## Prerequisites

- `tmux` (required, must be installed)
- `python3` with `rich` library (required for screenshot rendering)
- `Pillow` Python library (optional, for PNG screenshots — falls back to text if unavailable)

Check with: `which tmux && python3 -c "from rich.console import Console; print('ok')"`

If Pillow is missing and you need screenshots: `pip3 install Pillow`

## Core Capabilities

You have three operations, all implemented as scripts in this skill's `scripts/` directory:

### 1. Launch a TUI app

```bash
bash <skill-path>/scripts/tui_launch.sh <session-name> <command> [width] [height]
```

- `session-name`: unique tmux session identifier (e.g., `balatro`, `my-game`)
- `command`: the command to run (e.g., `./my-app`, `go run .`)
- `width`/`height`: terminal dimensions (optional)

**Terminal size matters a lot.** TUI apps adapt their layout to the terminal size. If the tmux session size doesn't match what the user normally sees, the layout will be different and you may miss (or hallucinate) UI issues. The script auto-detects size from `/dev/tty` or `$COLUMNS`/`$LINES`, falling back to 120x40. But when the user is present, **ask them for their terminal size** or have them run `tput cols && tput lines` in their normal terminal. This ensures you see exactly what they see.

Example:
```bash
# Auto-detect size
bash <skill-path>/scripts/tui_launch.sh mygame "./balatro-cli"

# Explicit size (preferred when user provides their terminal dimensions)
bash <skill-path>/scripts/tui_launch.sh mygame "./balatro-cli" 200 50
```

You can also resize an existing session:
```bash
tmux resize-window -t <session-name> -x <width> -y <height>
```

The app runs in a detached tmux session. You don't see it directly — you interact through the other two operations.

### 2. Send keystrokes

```bash
bash <skill-path>/scripts/tui_send.sh <session-name> <key> [delay_ms]
```

- `key`: any tmux key name — literal characters, or special keys like `Enter`, `Space`, `Left`, `Right`, `Up`, `Down`, `Tab`, `Escape`, `BSpace`, `C-c` (Ctrl+C)
- `delay_ms`: wait time in ms after sending (default: 500). Increase for slow apps or animations.

Examples:
```bash
bash <skill-path>/scripts/tui_send.sh mygame Enter        # press Enter
bash <skill-path>/scripts/tui_send.sh mygame Space        # press Space
bash <skill-path>/scripts/tui_send.sh mygame Right 200    # press Right, wait 200ms
bash <skill-path>/scripts/tui_send.sh mygame q            # press 'q'
bash <skill-path>/scripts/tui_send.sh mygame C-c          # Ctrl+C
```

For typing a string of text, send each character individually or use tmux's literal mode:
```bash
tmux send-keys -t mygame -l "hello world"   # types literal text
```

### 3. Capture the screen

```bash
python3 <skill-path>/scripts/tui_capture.py <session-name> [--mode text|screenshot] [--output path]
```

- `--mode text` (default): returns the plain text content of the terminal. This is precise, shows exact character positions and spacing. Good for analyzing layout alignment, text content, and structural issues.
- `--mode screenshot`: renders a PNG image of the terminal with colors. Save it to a file and use the Read tool to view it. Good for visual inspection of the overall look and color issues.
- `--output`: where to save (screenshot mode only). If omitted, saves to `/tmp/tui-interact/<session>/capture-<timestamp>.png` — one folder per session keeps test artifacts grouped together instead of littering `/tmp`.

Examples:
```bash
# Get text content (printed to stdout)
python3 <skill-path>/scripts/tui_capture.py mygame

# Take a visual screenshot
python3 <skill-path>/scripts/tui_capture.py mygame --mode screenshot --output /tmp/screen.png
# Then use Read tool on /tmp/screen.png to see it
```

### 4. Stop the app

```bash
bash <skill-path>/scripts/tui_stop.sh <session-name>
```

Kills the tmux session and cleans up.

## Workflow Pattern

A typical interaction loop looks like:

```
1. Launch the app
2. Capture screen → see current state
3. Decide what to do (this is YOUR job as the agent)
4. Send keystrokes
5. Capture screen → see result
6. Repeat 3-5
7. Stop when done
```

**The skill provides the mechanism; you provide the intelligence.** The skill does not decide what keys to press or what constitutes a bug — that's your responsibility based on the task context.

## Tips

- **Always capture after sending keys** to see the result of your action.
- **Increase delay** (`delay_ms`) if the app has animations or transitions — capturing too early will show an intermediate state.
- **Use text mode for analysis** (alignment, content checking) and **screenshot mode for visual review** (colors, overall appearance).
- **Terminal size is critical**: TUI apps adapt their layout to terminal dimensions. A mismatch means you're not seeing what the user sees. Before starting, ask the user for their terminal size (or have them run `tput cols && tput lines`). You can also resize mid-session with `tmux resize-window -t <session> -x <w> -y <h>`.
- **Multiple sessions**: you can run multiple apps simultaneously with different session names.
- **If the app crashes**, the tmux session stays open but shows the shell. Capture will show the crash output.
- **Chinese/CJK text in screenshots**: the rendering script tries to find a CJK-capable font. If characters show as boxes, text mode will still show them correctly.
- **For debugging layout issues**, text mode is often more useful than screenshots — you can count exact character positions and check alignment.
