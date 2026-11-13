"""Styles module for Markdown Viewer providing GitHub-style Light and Dark themes,
Pygments code syntax highlighting, GitHub alert banners, tables, and task lists.
"""

from pygments.formatters import HtmlFormatter

# Generate Pygments CSS for light (friendly) and dark (nord/monokai) themes
PYGMENTS_LIGHT = HtmlFormatter(style="friendly").get_style_defs(".codehilite")
PYGMENTS_DARK = HtmlFormatter(style="nord-darker").get_style_defs(".codehilite")

CSS_BASE = """
:root {
    --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji";
    --font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace;
    --transition-speed: 0.2s;
}

/* Light Theme Variables */
:root, html.light {
    --bg-primary: #ffffff;
    --bg-secondary: #f6f8fa;
    --bg-tertiary: #eaeef2;
    --text-primary: #1f2328;
    --text-secondary: #656d76;
    --border-color: #d0d7de;
    --border-subtle: #ebf0f4;
    --link-color: #0969da;
    --code-bg: #f6f8fa;
    --code-border: #d0d7de;
    --table-zebra: #f6f8fa;
    --blockquote-border: #d0d7de;
    --alert-note-bg: #ddf4ff;
    --alert-note-border: #0969da;
    --alert-tip-bg: #dafbe1;
    --alert-tip-border: #1a7f37;
    --alert-important-bg: #fbefff;
    --alert-important-border: #8250df;
    --alert-warning-bg: #fff8c5;
    --alert-warning-border: #9a6700;
    --alert-caution-bg: #ffebe9;
    --alert-caution-border: #cf222e;
}

/* Dark Theme Variables */
@media (prefers-color-scheme: dark) {
    :root:not(.light) {
        --bg-primary: #1c1c1e;
        --bg-secondary: #252528;
        --bg-tertiary: #303034;
        --text-primary: #e6edf3;
        --text-secondary: #9198a1;
        --border-color: #3d3d42;
        --border-subtle: #2d2d31;
        --link-color: #4493f8;
        --code-bg: #222226;
        --code-border: #3d3d42;
        --table-zebra: #242427;
        --blockquote-border: #444c56;
        --alert-note-bg: #0d263a;
        --alert-note-border: #388bfd;
        --alert-tip-bg: #102e1c;
        --alert-tip-border: #2ea043;
        --alert-important-bg: #271638;
        --alert-important-border: #a371f7;
        --alert-warning-bg: #2d2008;
        --alert-warning-border: #bb8009;
        --alert-caution-bg: #341212;
        --alert-caution-border: #f85149;
    }
}

html.dark {
    --bg-primary: #1c1c1e;
    --bg-secondary: #252528;
    --bg-tertiary: #303034;
    --text-primary: #e6edf3;
    --text-secondary: #9198a1;
    --border-color: #3d3d42;
    --border-subtle: #2d2d31;
    --link-color: #4493f8;
    --code-bg: #222226;
    --code-border: #3d3d42;
    --table-zebra: #242427;
    --blockquote-border: #444c56;
    --alert-note-bg: #0d263a;
    --alert-note-border: #388bfd;
    --alert-tip-bg: #102e1c;
    --alert-tip-border: #2ea043;
    --alert-important-bg: #271638;
    --alert-important-border: #a371f7;
    --alert-warning-bg: #2d2008;
    --alert-warning-border: #bb8009;
    --alert-caution-bg: #341212;
    --alert-caution-border: #f85149;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 0;
    background-color: var(--bg-primary);
    color: var(--text-primary);
    font-family: var(--font-sans);
    font-size: 16px;
    line-height: 1.6;
    word-wrap: break-word;
    -webkit-font-smoothing: antialiased;
    transition: background-color var(--transition-speed), color var(--transition-speed);
}

.markdown-container {
    max-width: 920px;
    margin: 0 auto;
    padding: 36px 32px 80px 32px;
}

/* Headings */
h1, h2, h3, h4, h5, h6 {
    margin-top: 28px;
    margin-bottom: 16px;
    font-weight: 600;
    line-height: 1.25;
    color: var(--text-primary);
    position: relative;
}

h1 {
    font-size: 2em;
    padding-bottom: 0.3em;
    border-bottom: 1px solid var(--border-color);
    margin-top: 0;
}

h2 {
    font-size: 1.5em;
    padding-bottom: 0.3em;
    border-bottom: 1px solid var(--border-subtle);
}

h3 { font-size: 1.25em; }
h4 { font-size: 1em; }
h5 { font-size: 0.875em; }
h6 { font-size: 0.85em; color: var(--text-secondary); }

p {
    margin-top: 0;
    margin-bottom: 16px;
}

a {
    color: var(--link-color);
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

hr {
    height: 0.25em;
    padding: 0;
    margin: 28px 0;
    background-color: var(--border-color);
    border: 0;
}

/* Lists */
ul, ol {
    margin-top: 0;
    margin-bottom: 16px;
    padding-left: 2em;
}

li {
    margin-top: 0.25em;
}

li + li {
    margin-top: 0.35em;
}

/* Task Lists */
ul.task-list {
    list-style-type: none;
    padding-left: 0;
}

.task-list-item {
    display: flex;
    align-items: flex-start;
    gap: 8px;
    margin-bottom: 6px;
}

.task-list-item input[type="checkbox"] {
    margin-top: 4px;
    accent-color: var(--link-color);
    width: 16px;
    height: 16px;
    cursor: default;
}

/* Blockquotes */
blockquote {
    margin: 0 0 16px 0;
    padding: 8px 16px;
    color: var(--text-secondary);
    border-left: 4px solid var(--blockquote-border);
    background-color: var(--bg-secondary);
    border-radius: 0 6px 6px 0;
}

blockquote > :last-child {
    margin-bottom: 0;
}

/* Tables */
table {
    border-spacing: 0;
    border-collapse: collapse;
    margin-top: 0;
    margin-bottom: 20px;
    width: 100%;
    overflow: auto;
    display: block;
    border-radius: 8px;
    border: 1px solid var(--border-color);
}

table th {
    font-weight: 600;
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    padding: 10px 14px;
    border-bottom: 1px solid var(--border-color);
    text-align: left;
}

table td {
    padding: 9px 14px;
    border-bottom: 1px solid var(--border-subtle);
}

table tr:nth-child(2n) td {
    background-color: var(--table-zebra);
}

table tr:last-child td {
    border-bottom: none;
}

/* Inline Code */
code:not([class*="language-"]):not(.hljs) {
    padding: 0.2em 0.4em;
    margin: 0;
    font-size: 85%;
    background-color: var(--code-bg);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    font-family: var(--font-mono);
}

/* Code Blocks with Header and Copy Button */
.code-block-wrapper {
    position: relative;
    margin-bottom: 20px;
    border: 1px solid var(--border-color);
    border-radius: 8px;
    background-color: var(--code-bg);
    overflow: hidden;
}

.code-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 12px;
    background-color: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    font-family: var(--font-mono);
    font-size: 12px;
    color: var(--text-secondary);
    user-select: none;
}

.code-lang {
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.5px;
}

.copy-button {
    background: transparent;
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    transition: all 0.15s ease;
}

.copy-button:hover {
    background: var(--bg-tertiary);
    color: var(--text-primary);
    border-color: var(--text-secondary);
}

.copy-button.copied {
    color: #2ea043;
    border-color: #2ea043;
}

.codehilite {
    margin: 0;
    padding: 0;
    background: transparent !important;
}

.codehilite pre {
    margin: 0;
    padding: 14px 16px;
    overflow-x: auto;
    font-family: var(--font-mono);
    font-size: 13.5px;
    line-height: 1.5;
}

/* GitHub Alerts */
.markdown-alert {
    padding: 12px 16px;
    margin-bottom: 18px;
    border-left: 4px solid;
    border-radius: 0 8px 8px 0;
    font-size: 14.5px;
}

.markdown-alert-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    margin-bottom: 6px;
}

.markdown-alert-title svg {
    width: 16px;
    height: 16px;
    flex-shrink: 0;
}

.markdown-alert-note {
    background-color: var(--alert-note-bg);
    border-color: var(--alert-note-border);
    color: var(--text-primary);
}
.markdown-alert-note .markdown-alert-title { color: var(--alert-note-border); }

.markdown-alert-tip {
    background-color: var(--alert-tip-bg);
    border-color: var(--alert-tip-border);
    color: var(--text-primary);
}
.markdown-alert-tip .markdown-alert-title { color: var(--alert-tip-border); }

.markdown-alert-important {
    background-color: var(--alert-important-bg);
    border-color: var(--alert-important-border);
    color: var(--text-primary);
}
.markdown-alert-important .markdown-alert-title { color: var(--alert-important-border); }

.markdown-alert-warning {
    background-color: var(--alert-warning-bg);
    border-color: var(--alert-warning-border);
    color: var(--text-primary);
}
.markdown-alert-warning .markdown-alert-title { color: var(--alert-warning-border); }

.markdown-alert-caution {
    background-color: var(--alert-caution-bg);
    border-color: var(--alert-caution-border);
    color: var(--text-primary);
}
.markdown-alert-caution .markdown-alert-title { color: var(--alert-caution-border); }

/* Images */
img {
    max-width: 100%;
    height: auto;
    border-radius: 6px;
    margin: 8px 0;
}

/* Scrollbars */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background-color: var(--border-color);
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background-color: var(--text-secondary);
}
"""

def get_complete_css() -> str:
    """Return full compiled CSS including theme overrides and pygments code styles."""
    return f"""
    {CSS_BASE}
    
    /* Pygments Light */
    @media (prefers-color-scheme: light) {{
        {PYGMENTS_LIGHT}
    }}
    html.light {PYGMENTS_LIGHT}
    
    /* Pygments Dark */
    @media (prefers-color-scheme: dark) {{
        :root:not(.light) {PYGMENTS_DARK}
    }}
    html.dark {PYGMENTS_DARK}
    """
