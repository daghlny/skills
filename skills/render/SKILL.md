---
name: render
description: "Renders the most recent Claude response as a beautifully formatted HTML page with proper LaTeX math formula rendering and syntax-highlighted code blocks. Use this skill whenever the user types /render, or asks to render, preview, or view the last response with proper formatting -- especially when the response contains math formulas that display poorly in the terminal."
---

# Render Last Response

This skill is a **pure program**. It reads the current session's transcript
directly, extracts the last assistant response, renders it to a self-contained
HTML page (LaTeX via KaTeX, code via highlight.js, markdown via marked.js — all
bundled locally for zero network requests), and opens it in the browser.

Do **not** regenerate, re-emit, or reformat the previous response yourself —
that is what caused the old latency. Just run the script.

## Steps

Run this single command (no other action needed). If you know where this skill
is installed (normally `~/.claude/skills/render/`):

```bash
python3 ~/.claude/skills/render/render.py
```

If unsure of the install location, locate it first:

```bash
python3 "$(find ~/.claude ~/.codex ~/.agent -maxdepth 4 -name render.py -path '*render*' 2>/dev/null | head -1)"
```

The script:
1. Maps the working directory to its `~/.claude/projects/<encoded>/` transcript
   directory and picks the most recently modified `*.jsonl` session file.
2. Finds the last genuine user turn (the one that invoked `/render`) and takes
   the last assistant **text** response before it — this is the response to
   render, regardless of any preamble in the current turn.
3. Writes `/tmp/claude_render.html` and opens it (`open` on macOS,
   `xdg-open` on Linux).

After it runs, tell the user briefly: "Already opened in your browser."

## Notes

- The script lives next to this `SKILL.md` as `render.py`; the `assets/`
  directory next to it holds `katex.min.css`, `katex.min.js`,
  `auto-render.min.js`, `marked.min.js`, `highlight.min.js`, `github.min.css`,
  and a `fonts/` folder. All are referenced via `file://` URLs.
- The script needs only `python3` (standard library only — no pip installs).
- If the script reports "No assistant response found", the session has no prior
  assistant message yet (e.g. a brand-new session).
