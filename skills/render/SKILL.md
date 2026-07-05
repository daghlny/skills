---
name: render
description: "Renders the most recent Claude response as a beautifully formatted HTML page with proper LaTeX math formula rendering, syntax-highlighted code blocks, and mermaid diagrams. Use this skill whenever the user types /render, or asks to render, preview, or view the last response with proper formatting -- especially when the response contains math formulas or diagrams that display poorly in the terminal."
---

# Render Last Response

This skill is a **pure program**. It reads the current session's transcript
directly, extracts the last assistant response, renders it to a single
self-contained HTML page, and opens it in the browser.

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

## What it renders

- **Markdown** via marked (GFM: tables, task lists, blockquotes, …)
- **Math** via KaTeX — inline `$...$` / `\(...\)` and display `$$...$$` /
  `\[...\]`. Math is tokenized as a marked extension *before* markdown inline
  rules run, so `$x_i$` is never mangled into emphasis; code blocks/spans are
  skipped; bare prices like "$5 and $10" are left alone.
- **Code** via highlight.js (applied post-parse with `highlightElement`).
- **Diagrams** via mermaid for ` ```mermaid ` fences (flowchart, sequence, …).

## Offline / no-blank-page guarantees

- All CSS and JS libraries are **inlined into the output HTML** — the page
  keeps working even if the skill directory later moves. Only KaTeX fonts are
  referenced via `file://` (a failed font load merely degrades typography).
- mermaid (~3.5 MB) is inlined only when the content actually contains a
  mermaid fence; other pages are ~450 KB.
- A missing library asset makes the script **fail loudly** instead of writing
  a page that would blank on load.
- If in-page rendering still throws, the page falls back to showing the raw
  markdown as plain text with an error banner — never a blank page.

## Notes

- The script lives next to this `SKILL.md` as `render.py`; the `assets/`
  directory holds `katex.min.css`, `katex.min.js`, `marked.min.js`,
  `highlight.min.js`, `mermaid.min.js`, `github.min.css`, and a `fonts/`
  folder.
- The script needs only `python3` (standard library only — no pip installs).
- `render.py --md FILE` renders an arbitrary markdown file (useful for
  testing the pipeline).
- If the script reports "No assistant response found", the session has no
  prior assistant message yet (e.g. a brand-new session).
