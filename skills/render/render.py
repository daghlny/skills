#!/usr/bin/env python3
"""Render the most recent Claude response as a self-contained HTML page.

This is a pure program: it reads the current session's transcript directly,
extracts the last assistant text response, fills the HTML template with
locally-bundled rendering libraries, and opens it in the browser. No model
involvement is required, so there is no "thinking" latency.

Usage:
    render.py            # uses $PWD to locate the project transcript
    render.py /path/dir  # treat the given dir as the working directory
"""

import glob
import html
import json
import os
import subprocess
import sys
import urllib.parse

OUT_PATH = "/tmp/claude_render.html"


def project_transcript_dir(cwd):
    """Map a working directory to its Claude transcript directory."""
    # Claude Code encodes the project path by replacing every "/" with "-".
    encoded = cwd.replace("/", "-")
    return os.path.join(os.path.expanduser("~/.claude/projects"), encoded)


def latest_transcript(cwd):
    proj_dir = project_transcript_dir(cwd)
    files = glob.glob(os.path.join(proj_dir, "*.jsonl"))
    if not files:
        sys.exit(f"No transcript found in {proj_dir}")
    return max(files, key=os.path.getmtime)


def is_human_turn(entry):
    """True if entry is a genuine user input (not a tool_result)."""
    msg = entry.get("message")
    if not isinstance(msg, dict) or msg.get("role") != "user":
        return False
    content = msg.get("content")
    if isinstance(content, str):
        return True
    if isinstance(content, list):
        # A real human turn has no tool_result blocks.
        return not any(
            isinstance(b, dict) and b.get("type") == "tool_result" for b in content
        )
    return False


def assistant_text(entry):
    """Return concatenated text blocks of an assistant message, or None."""
    msg = entry.get("message")
    if not isinstance(msg, dict) or msg.get("role") != "assistant":
        return None
    content = msg.get("content")
    if not isinstance(content, list):
        return None
    parts = [
        b.get("text", "")
        for b in content
        if isinstance(b, dict) and b.get("type") == "text"
    ]
    text = "".join(parts).strip()
    return text or None


def last_response(transcript):
    entries = []
    with open(transcript) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    # Find the last genuine human turn (the one that invoked /render).
    cutoff = len(entries)
    for i in range(len(entries) - 1, -1, -1):
        if is_human_turn(entries[i]):
            cutoff = i
            break

    # The response to render is the last assistant text strictly before it.
    for i in range(cutoff - 1, -1, -1):
        text = assistant_text(entries[i])
        if text:
            return text

    sys.exit("No assistant response found to render.")


REQUIRED_ASSETS = [
    "katex.min.css",
    "github.min.css",
    "katex.min.js",
    "auto-render.min.js",
    "marked.min.js",
    "highlight.min.js",
]


def check_assets(assets_dir):
    """Fail loudly if a required local asset is missing (avoids a silent
    blank page where one un-loaded script breaks JS rendering)."""
    missing = [a for a in REQUIRED_ASSETS if not os.path.isfile(os.path.join(assets_dir, a))]
    if missing:
        sys.exit(
            "Missing rendering assets in {0}:\n  {1}\n"
            "The page renders via JavaScript, so a missing library would show a "
            "blank page. Re-run the skill's install/sync to restore assets/.".format(
                assets_dir, "\n  ".join(missing)
            )
        )


def build_html(markdown, assets_dir):
    assets_url = "file://" + urllib.parse.quote(assets_dir)
    escaped = html.escape(markdown, quote=False)
    return TEMPLATE.replace("__ASSETS__", assets_url).replace(
        "__CONTENT__", escaped
    )


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Claude Response</title>
<link rel="stylesheet" href="__ASSETS__/katex.min.css">
<link rel="stylesheet" href="__ASSETS__/github.min.css">
<style>
  body {
    max-width: 800px;
    margin: 40px auto;
    padding: 0 20px;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
    font-size: 16px;
    line-height: 1.7;
    color: #24292e;
    background: #fff;
  }
  h1, h2, h3 { margin-top: 1.5em; margin-bottom: 0.5em; }
  h1 { font-size: 1.8em; border-bottom: 1px solid #eee; padding-bottom: 0.3em; }
  h2 { font-size: 1.4em; border-bottom: 1px solid #eee; padding-bottom: 0.2em; }
  pre {
    background: #f6f8fa;
    border-radius: 6px;
    padding: 16px;
    overflow-x: auto;
    font-size: 14px;
    line-height: 1.5;
  }
  code { font-family: "SF Mono", "Fira Code", Menlo, monospace; font-size: 0.9em; }
  p code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
  .katex-display { margin: 1.2em 0; overflow-x: auto; }
  blockquote { border-left: 4px solid #dfe2e5; margin: 0; padding: 0 1em; color: #6a737d; }
  ul, ol { padding-left: 2em; }
  li { margin: 0.3em 0; }
  strong { font-weight: 600; }
</style>
</head>
<body>
<div id="raw-content" style="display:none;">
__CONTENT__
</div>
<div id="rendered"></div>

<script src="__ASSETS__/katex.min.js"></script>
<script src="__ASSETS__/auto-render.min.js"></script>
<script src="__ASSETS__/marked.min.js"></script>
<script src="__ASSETS__/highlight.min.js"></script>
<script>
  const raw = document.getElementById('raw-content').textContent;
  const target = document.getElementById('rendered');
  try {
    if (typeof marked === 'undefined') throw new Error('marked.js failed to load');
    if (typeof hljs !== 'undefined') {
      marked.setOptions({
        highlight: function(code, lang) {
          if (lang && hljs.getLanguage(lang)) {
            return hljs.highlight(code, {language: lang}).value;
          }
          return code;
        }
      });
    }
    target.innerHTML = marked.parse(raw);
    if (typeof renderMathInElement !== 'undefined') {
      renderMathInElement(target, {
        delimiters: [
          {left: '$$', right: '$$', display: true},
          {left: '$', right: '$', display: false}
        ],
        throwOnError: false
      });
    }
  } catch (e) {
    // Never show a blank page: fall back to the raw markdown as plain text.
    const pre = document.createElement('pre');
    pre.style.whiteSpace = 'pre-wrap';
    pre.textContent = raw;
    target.innerHTML = '';
    target.appendChild(
      Object.assign(document.createElement('div'), {
        style: 'color:#b00;font-size:13px;margin-bottom:1em',
        textContent: 'Rich rendering failed (' + e.message + '); showing raw text.'
      })
    );
    target.appendChild(pre);
  }
</script>
</body>
</html>
"""


def main():
    cwd = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PWD", os.getcwd())
    cwd = os.path.abspath(cwd)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(script_dir, "assets")

    transcript = latest_transcript(cwd)
    markdown = last_response(transcript)
    page = build_html(markdown, assets_dir)
    with open(OUT_PATH, "w") as f:
        f.write(page)

    opener = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.run([opener, OUT_PATH], check=False)
    print(f"Rendered last response -> {OUT_PATH} (opened in browser).")


if __name__ == "__main__":
    main()
