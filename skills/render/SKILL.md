---
name: render
description: "Renders the most recent Claude response as a beautifully formatted HTML page with proper LaTeX math formula rendering and syntax-highlighted code blocks. Use this skill whenever the user types /render, or asks to render, preview, or view the last response with proper formatting -- especially when the response contains math formulas that display poorly in the terminal."
---

# Render Last Response

When this skill is invoked, take your most recent response from the conversation and render it as a well-formatted HTML page with proper math and code rendering.

## Steps

1. Identify your most recent response in the conversation (the one immediately before the user invoked `/render`).

2. Write a self-contained HTML file to `/tmp/claude_render.html` that:
   - Includes the full response content
   - Uses KaTeX (via CDN) for math rendering
   - Uses marked.js (via CDN) for Markdown-to-HTML conversion
   - Uses highlight.js (via CDN) for syntax-highlighted code blocks
   - Has clean, readable typography

3. Open it in the default browser: `open /tmp/claude_render.html`

## HTML Template

Use this exact template structure. Place the raw markdown content of your last response inside the `#raw-content` div, with HTML special characters escaped (`<` as `&lt;`, `>` as `&gt;`, `&` as `&amp;`). This is critical -- the content must be escaped so the browser doesn't interpret markdown/LaTeX as HTML tags.

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Claude Response</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/github.min.css">
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

<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/contrib/auto-render.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/lib/core.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/lib/languages/python.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/lib/languages/javascript.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/lib/languages/bash.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/lib/languages/json.min.js"></script>
<script>
  hljs.registerLanguage('python', hljs.getLanguage('python') || function(){return{}});

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

- Escape all HTML special characters in the markdown content before inserting into the `#raw-content` div. The `<`, `>`, and `&` characters must be escaped as `&lt;`, `&gt;`, and `&amp;` respectively, otherwise the browser will try to parse markdown as HTML.
- Keep the content exactly as it was in the original response -- do not summarize, trim, or rephrase.
- After opening the browser, tell the user briefly: "Already opened in your browser."
