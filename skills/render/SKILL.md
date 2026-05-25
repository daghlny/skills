---
name: render
description: "Renders the most recent Claude response as a beautifully formatted HTML page with proper LaTeX math formula rendering and syntax-highlighted code blocks. Use this skill whenever the user types /render, or asks to render, preview, or view the last response with proper formatting -- especially when the response contains math formulas that display poorly in the terminal."
---

# Render Last Response

When this skill is invoked, take your most recent response from the conversation and render it as a well-formatted HTML page with proper math and code rendering.

All rendering libraries (KaTeX, marked.js, highlight.js) and the KaTeX fonts are
bundled locally in this skill's `assets/` directory. The generated page loads
them from disk via `file://` URLs and makes **zero network requests**, so it
renders correctly on any machine even with no internet or a blocked CDN.

## Steps

1. Identify your most recent response in the conversation (the one immediately before the user invoked `/render`).

2. Determine the absolute path to this skill's `assets/` directory. It sits next
   to this `SKILL.md` file (the skill is normally installed at
   `~/.claude/skills/render/assets`). Resolve `~`/`$HOME` to the real absolute
   path — e.g. run `echo "$HOME/.claude/skills/render/assets"` if unsure. Call
   this absolute path `ASSETS_DIR`.

3. Write a self-contained HTML file to `/tmp/claude_render.html` using the
   template below. Replace every `ASSETS_DIR` placeholder with
   `file://<the absolute assets path>` (for example
   `file:///Users/you/.claude/skills/render/assets`). Place the raw markdown of
   your last response inside the `#raw-content` div.

4. Open it in the default browser: `open /tmp/claude_render.html`

## HTML Template

Use this exact template structure. Place the raw markdown content of your last response inside the `#raw-content` div, with HTML special characters escaped (`<` as `&lt;`, `>` as `&gt;`, `&` as `&amp;`). This is critical -- the content must be escaped so the browser doesn't interpret markdown/LaTeX as HTML tags.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Claude Response</title>
<link rel="stylesheet" href="ASSETS_DIR/katex.min.css">
<link rel="stylesheet" href="ASSETS_DIR/github.min.css">
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
YOUR_ESCAPED_MARKDOWN_HERE
</div>
<div id="rendered"></div>

<script src="ASSETS_DIR/katex.min.js"></script>
<script src="ASSETS_DIR/auto-render.min.js"></script>
<script src="ASSETS_DIR/marked.min.js"></script>
<script src="ASSETS_DIR/highlight.min.js"></script>
<script>
  marked.setOptions({
    highlight: function(code, lang) {
      if (lang && hljs.getLanguage(lang)) {
        return hljs.highlight(code, {language: lang}).value;
      }
      return code;
    }
  });

  const raw = document.getElementById('raw-content').textContent;
  document.getElementById('rendered').innerHTML = marked.parse(raw);

  renderMathInElement(document.getElementById('rendered'), {
    delimiters: [
      {left: '$$', right: '$$', display: true},
      {left: '$', right: '$', display: false}
    ],
    throwOnError: false
  });
</script>
</body>
</html>
```

## Important Notes

- The `assets/` directory must ship with the skill. It contains: `katex.min.css`, `katex.min.js`, `auto-render.min.js`, `marked.min.js`, `highlight.min.js`, `github.min.css`, and a `fonts/` folder with KaTeX `.woff2` files. The KaTeX CSS references the fonts via relative `fonts/...` URLs, so the `fonts/` folder must stay next to `katex.min.css`.
- Replace **every** `ASSETS_DIR` in the template with the same `file://` absolute path. Do not leave any `ASSETS_DIR` placeholder or any `https://` CDN URL in the output -- the whole point is to avoid network requests.
- Escape all HTML special characters in the markdown content before inserting into the `#raw-content` div. The `<`, `>`, and `&` characters must be escaped as `&lt;`, `&gt;`, and `&amp;` respectively, otherwise the browser will try to parse markdown as HTML.
- Keep the content exactly as it was in the original response -- do not summarize, trim, or rephrase.
- After opening the browser, tell the user briefly: "Already opened in your browser."
