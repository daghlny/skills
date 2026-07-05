#!/usr/bin/env python3
"""Render the most recent Claude response as a self-contained HTML page.

This is a pure program: it reads the current session's transcript directly,
extracts the last assistant text response, inlines all rendering libraries
(marked, KaTeX, highlight.js, mermaid) into a single HTML file, and opens it
in the browser. No model involvement, no network requests.

Usage:
    render.py              # uses $PWD to locate the project transcript
    render.py /path/dir    # treat the given dir as the working directory
    render.py --md FILE    # render an arbitrary markdown file (for testing)
"""

import glob
import html
import json
import os
import re
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
    "marked.min.js",
    "highlight.min.js",
    "mermaid.min.js",
]


def read_asset(assets_dir, name):
    path = os.path.join(assets_dir, name)
    if not os.path.isfile(path):
        sys.exit(
            f"Missing rendering asset: {path}\n"
            "Re-run the skill's install/sync to restore assets/."
        )
    with open(path, encoding="utf-8") as f:
        return f.read()


def safe_inline_js(js):
    """Make JS safe to embed in a <script> tag: a literal '</script' inside
    the source (even in a string) would terminate the tag early."""
    return js.replace("</script", "<\\/script").replace("<!--", "<\\!--")


def build_html(markdown, assets_dir):
    katex_css = read_asset(assets_dir, "katex.min.css")
    # The KaTeX css references fonts relatively; the output page lives in
    # /tmp, so rewrite them to absolute file:// URLs (a failed font load only
    # degrades typography — it can't blank the page).
    fonts_url = "file://" + urllib.parse.quote(os.path.join(assets_dir, "fonts"))
    katex_css = katex_css.replace("url(fonts/", f"url({fonts_url}/")

    scripts = [
        read_asset(assets_dir, "katex.min.js"),
        read_asset(assets_dir, "marked.min.js"),
        read_asset(assets_dir, "highlight.min.js"),
    ]
    # mermaid is ~3.5 MB — only inline it when the content actually has a
    # mermaid code fence.
    if re.search(r"^\s*(`{3,}|~{3,})\s*mermaid\b", markdown, re.M):
        scripts.append(read_asset(assets_dir, "mermaid.min.js"))

    libs_js = safe_inline_js("\n;\n".join(scripts))
    escaped = html.escape(markdown, quote=False)

    page = TEMPLATE
    page = page.replace("__KATEX_CSS__", katex_css)
    page = page.replace("__HLJS_CSS__", read_asset(assets_dir, "github.min.css"))
    page = page.replace("__LIBS_JS__", libs_js)
    page = page.replace("__CONTENT__", escaped)
    return page


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Claude Response</title>
<style>__KATEX_CSS__</style>
<style>__HLJS_CSS__</style>
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
  p code, li code, td code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
  .katex-display { margin: 1.2em 0; overflow-x: auto; }
  blockquote { border-left: 4px solid #dfe2e5; margin: 0; padding: 0 1em; color: #6a737d; }
  ul, ol { padding-left: 2em; }
  li { margin: 0.3em 0; }
  strong { font-weight: 600; }
  table { border-collapse: collapse; margin: 1em 0; display: block; overflow-x: auto; }
  th, td { border: 1px solid #dfe2e5; padding: 6px 13px; }
  th { background: #f6f8fa; font-weight: 600; }
  tr:nth-child(2n) td { background: #fafbfc; }
  img { max-width: 100%; }
  hr { border: 0; border-top: 1px solid #eee; margin: 2em 0; }
  pre.mermaid { background: #fff; text-align: center; }
</style>
</head>
<body>
<div id="raw-content" style="display:none;">
__CONTENT__
</div>
<div id="rendered"></div>

<script>__LIBS_JS__</script>
<script>
(function () {
  const raw = document.getElementById('raw-content').textContent
    .replace(/^\\n+/, '').replace(/\\n+$/, '');
  const target = document.getElementById('rendered');

  function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function tex(src, display) {
    try {
      return katex.renderToString(src, {displayMode: display, throwOnError: false});
    } catch (e) {
      return '<code>' + escapeHtml(src) + '</code>';
    }
  }

  try {
    if (typeof marked === 'undefined') throw new Error('marked.js failed to load');

    // Math is handled as marked extensions so it is tokenized BEFORE the
    // markdown inline rules run — otherwise `$x_i$` gets mangled into
    // emphasis. Code blocks/spans are naturally skipped by the tokenizer.
    const blockMath = {
      name: 'blockMath', level: 'block',
      tokenizer(src) {
        const m = src.match(/^\\$\\$([\\s\\S]+?)\\$\\$/) ||
                  src.match(/^\\\\\\[([\\s\\S]+?)\\\\\\]/);
        if (m) return {type: 'blockMath', raw: m[0], text: m[1].trim()};
      },
      renderer(t) { return tex(t.text, true); }
    };
    const inlineMath = {
      name: 'inlineMath', level: 'inline',
      start(src) {
        const m = src.match(/\\$|\\\\\\(/);
        return m ? m.index : undefined;
      },
      tokenizer(src) {
        let m = src.match(/^\\$\\$([\\s\\S]+?)\\$\\$/);
        if (m) return {type: 'inlineMath', raw: m[0], text: m[1].trim(), display: true};
        // $...$: no space just inside the delimiters, no digit right after
        // the closing $ (avoids matching prices like "$5 and $10").
        m = src.match(/^\\$(?!\\s)((?:\\\\.|[^\\\\$\\n])+?)\\$(?!\\d)/);
        if (m && !/\\s$/.test(m[1]))
          return {type: 'inlineMath', raw: m[0], text: m[1], display: false};
        m = src.match(/^\\\\\\(([\\s\\S]+?)\\\\\\)/);
        if (m) return {type: 'inlineMath', raw: m[0], text: m[1].trim(), display: false};
      },
      renderer(t) { return tex(t.text, t.display); }
    };
    marked.use({extensions: [blockMath, inlineMath]});

    // Route ```mermaid fences to a <pre class="mermaid"> for mermaid.run();
    // everything else falls through to the default code renderer.
    marked.use({
      renderer: {
        code(code, infostring) {
          const lang = (infostring || '').trim().split(/\\s+/)[0];
          if (lang === 'mermaid')
            return '<pre class="mermaid">' + escapeHtml(code) + '</pre>';
          return false;
        }
      }
    });

    target.innerHTML = marked.parse(raw);

    if (typeof hljs !== 'undefined') {
      target.querySelectorAll('pre code').forEach(function (el) {
        try { hljs.highlightElement(el); } catch (e) {}
      });
    }

    if (typeof mermaid !== 'undefined' && target.querySelector('.mermaid')) {
      mermaid.initialize({startOnLoad: false, theme: 'default', securityLevel: 'loose'});
      mermaid.run({querySelector: '#rendered .mermaid'}).catch(function (e) {
        console.error('mermaid render failed:', e);
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
})();
</script>
</body>
</html>
"""


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(script_dir, "assets")

    if len(sys.argv) > 2 and sys.argv[1] == "--md":
        with open(sys.argv[2], encoding="utf-8") as f:
            markdown = f.read()
    else:
        cwd = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PWD", os.getcwd())
        cwd = os.path.abspath(cwd)
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
