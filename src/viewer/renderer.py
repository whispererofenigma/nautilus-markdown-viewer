"""Markdown Renderer module that transforms raw Markdown into styled, interactive HTML.
Includes support for GitHub Alerts, Code Copying, Task Lists, Table of Contents,
and Reading Metrics.
"""

import os
import html
import json
import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Tuple
import markdown
from pygments.formatters import HtmlFormatter
from markdown.extensions import Extension
from markdown.preprocessors import Preprocessor
from markdown.treeprocessors import Treeprocessor

from styles import get_complete_css

# SVG Icons for GitHub Alerts
ALERT_ICONS = {
    "NOTE": '<svg viewBox="0 0 16 16" fill="currentColor"><path d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8Zm8-6.5a6.5 6.5 0 1 0 0 13 6.5 6.5 0 0 0 0-13ZM6.5 7.75A.75.75 0 0 1 7.25 7h1a.75.75 0 0 1 .75.75v2.75h.25a.75.75 0 0 1 0 1.5h-2a.75.75 0 0 1 0-1.5h.25v-2h-.25a.75.75 0 0 1-.75-.75ZM8 6a1 1 0 1 1 0-2 1 1 0 0 1 0 2Z"></path></svg>',
    "TIP": '<svg viewBox="0 0 16 16" fill="currentColor"><path d="M8 1.5c-2.363 0-4 1.69-4 3.75 0 .984.424 1.625.984 2.304l.214.253c.223.264.47.556.673.848.284.411.537.896.621 1.49a.75.75 0 0 1-1.484.21c-.04-.282-.163-.534-.36-.82a8.01 8.01 0 0 0-.744-.937l-.216-.255C3.003 7.565 2.5 6.643 2.5 5.25 2.5 2.378 4.793 0 8 0s5.5 2.378 5.5 5.25c0 1.393-.503 2.315-1.168 3.107l-.216.255c-.23.272-.48.567-.744.937-.197.286-.32.538-.36.82a.75.75 0 0 1-1.484-.21c.084-.594.337-1.079.621-1.49.203-.292.45-.584.673-.848.075-.088.147-.173.214-.253.56-.679.984-1.32.984-2.304 0-2.06-1.637-3.75-4-3.75ZM5.75 12h4.5a.75.75 0 0 1 0 1.5h-4.5a.75.75 0 0 1 0-1.5Zm1 3h2.5a.75.75 0 0 1 0 1.5h-2.5a.75.75 0 0 1 0-1.5Z"></path></svg>',
    "IMPORTANT": '<svg viewBox="0 0 16 16" fill="currentColor"><path d="M0 1.75C0 .784.784 0 1.75 0h12.5C15.216 0 16 .784 16 1.75v9.5A1.75 1.75 0 0 1 14.25 13H9.06l-2.573 2.573A1.458 1.458 0 0 1 4 14.543V13H1.75A1.75 1.75 0 0 1 0 11.25Zm1.75-.25a.25.25 0 0 0-.25.25v9.5c0 .138.112.25.25.25h2.5a.75.75 0 0 1 .75.75v2.19l2.72-2.72a.749.749 0 0 1 .53-.22h6.75a.25.25 0 0 0 .25-.25v-9.5a.25.25 0 0 0-.25-.25Zm7 2.25v2.5a.75.75 0 0 1-1.5 0v-2.5a.75.75 0 0 1 1.5 0ZM9 9a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"></path></svg>',
    "WARNING": '<svg viewBox="0 0 16 16" fill="currentColor"><path d="M6.457 1.047c.659-1.234 2.427-1.234 3.086 0l6.082 11.378A1.75 1.75 0 0 1 14.082 15H1.918a1.75 1.75 0 0 1-1.543-2.575Zm1.763.707a.25.25 0 0 0-.44 0L1.698 13.132a.25.25 0 0 0 .22.368h12.164a.25.25 0 0 0 .22-.368Zm.53 3.996v2.5a.75.75 0 0 1-1.5 0v-2.5a.75.75 0 0 1 1.5 0ZM9 11a1 1 0 1 1-2 0 1 1 0 0 1 2 0Z"></path></svg>',
    "CAUTION": '<svg viewBox="0 0 16 16" fill="currentColor"><path d="M4.47.047A1.75 1.75 0 0 1 5.707 0h4.586c.464 0 .909.184 1.237.513l3.956 3.956c.329.328.514.773.514 1.237v4.586a1.75 1.75 0 0 1-.514 1.237l-3.956 3.956a1.75 1.75 0 0 1-1.237.513H5.707a1.75 1.75 0 0 1-1.237-.513L.514 11.53A1.75 1.75 0 0 1 0 10.293V5.707c0-.464.184-.909.513-1.237ZM5.707 1.5a.25.25 0 0 0-.177.073L1.573 5.53a.25.25 0 0 0-.073.177v4.586c0 .066.026.13.073.177l3.957 3.957c.047.047.111.073.177.073h4.586a.25.25 0 0 0 .177-.073l3.957-3.957a.25.25 0 0 0 .073-.177V5.707a.25.25 0 0 0-.073-.177L9.87 1.573A.25.25 0 0 0 9.693 1.5ZM8 4a.75.75 0 0 1 .75.75v3.5a.75.75 0 0 1-1.5 0v-3.5A.75.75 0 0 1 8 4Zm0 8a1 1 0 1 1 0-2 1 1 0 0 1 0 2Z"></path></svg>',
}


class LanguageFormatter(HtmlFormatter):
    def __init__(self, lang_str="language-text", **options):
        super().__init__(**options)
        self.cssclass = "codehilite " + lang_str


class AlertProcessor(Preprocessor):
    def run(self, lines):
        # Fenced code has already been stashed by the fenced_code extension.
        return MarkdownRenderer.preprocess_alerts("\n".join(lines)).split("\n")


class MathProcessor(Preprocessor):
    """Keep TeX delimiters and underscores intact until MathJax sees the DOM."""

    pattern = re.compile(
        r"(?P<indent>^(?: {4}|\t)[^\n]*(?:\n|$))|"
        r"(?P<code>`+[^`]*`+)|"
        r"(?P<math>\\\[.*?\\\]|\\\(.*?\\\)|"
        r"(?<!\\)\$\$.*?(?<!\\)\$\$|"
        r"(?<!\\)\$(?!\$)[^\n$]+?(?<!\\)\$(?!\$))",
        re.DOTALL | re.MULTILINE,
    )

    def run(self, lines):
        def preserve(match):
            if match.group("code") or match.group("indent"):
                return match.group(0)
            equation = html.escape(match.group("math"))
            return self.md.htmlStash.store(f'<span class="math">{equation}</span>')

        return self.pattern.sub(preserve, "\n".join(lines)).split("\n")


class TaskProcessor(Treeprocessor):
    def run(self, root):
        for item in root.iter("li"):
            target = item.find("p")
            if target is None:
                target = item
            match = re.match(r"^\[([ xX])\]\s+", target.text or "")
            if match:
                target.text = target.text[match.end() :]
                checkbox = ET.Element(
                    "input",
                    {
                        "type": "checkbox",
                        "disabled": "disabled",
                        "aria-label": "Task status",
                    },
                )
                if match.group(1).lower() == "x":
                    checkbox.set("checked", "checked")
                checkbox.tail, target.text = " " + target.text, None
                target.insert(0, checkbox)
                item.set("class", "task-list-item")


class PreviewExtension(Extension):
    def extendMarkdown(self, md):
        md.preprocessors.register(AlertProcessor(md), "github_alerts", 24)
        md.preprocessors.register(MathProcessor(md), "math", 23)
        md.treeprocessors.register(TaskProcessor(md), "task_lists", 15)


class MarkdownRenderer:
    def __init__(self, fragment=False):
        self.fragment = fragment
        self.md_parser = markdown.Markdown(
            extensions=[
                "fenced_code",
                "md_in_html",
                PreviewExtension(),
                "tables",
                "toc",
                "nl2br",
                "sane_lists",
                "codehilite",
            ],
            extension_configs={
                "codehilite": {
                    "guess_lang": False,
                    "pygments_formatter": LanguageFormatter,
                    "css_class": "codehilite",
                    "use_pygments": True,
                },
                "toc": {
                    "permalink": False,
                },
            },
        )

    @staticmethod
    def preprocess_alerts(text: str) -> str:
        """Preprocesses GitHub-style alerts (> [!NOTE]) into styled HTML blocks."""
        alert_types = r"(NOTE|TIP|IMPORTANT|WARNING|CAUTION)"
        pattern = re.compile(
            r"^>[ \t]*\[!" + alert_types + r"\][ \t]*\n((?:^>[ \t]*.*$\n?)+)",
            re.MULTILINE | re.IGNORECASE,
        )

        def repl(m):
            atype = m.group(1).upper()
            content_lines = m.group(2).splitlines()
            stripped = [re.sub(r"^>[ \t]?", "", line) for line in content_lines]
            body = "\n".join(stripped)
            icon = ALERT_ICONS.get(atype, "")
            return (
                f'<div class="markdown-alert markdown-alert-{atype.lower()}" markdown="1">\n'
                f'<div class="markdown-alert-title">{icon} {atype.capitalize()}</div>\n\n'
                f"{body}\n\n"
                f"</div>\n"
            )

        return pattern.sub(repl, text)

    def postprocess_code_blocks(self, html: str) -> str:
        """Wraps pygments code blocks in a styled card with language badge and copy button."""
        pattern = re.compile(
            r'(<div class="codehilite[^"]*">)(<pre><span></span><code>|<pre>)(.*?)(</code></pre>|</pre>)(</div>)',
            re.DOTALL,
        )

        def repl(match):
            full_match = match.group(0)

            # Try to detect language from class or comments
            lang_match = re.search(r"language-([a-zA-Z0-9_+.-]+)", full_match)
            lang = lang_match.group(1) if lang_match else "code"

            return (
                f'<div class="code-block-wrapper">'
                f'  <div class="code-header">'
                f'    <span class="code-lang">{lang}</span>'
                f'    <button class="copy-button" onclick="copySnippet(this)">'
                f'      <svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor">'
                f'        <path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 0 1 0 1.5h-1.5a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-1.5a.75.75 0 0 1 1.5 0v1.5A1.75 1.75 0 0 1 9.25 16h-7.5A1.75 1.75 0 0 1 0 14.25Z"></path>'
                f'        <path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0 1 14.25 11h-7.5A1.75 1.75 0 0 1 5 9.25Zm1.75-.25a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-7.5a.25.25 0 0 0-.25-.25Z"></path>'
                f"      </svg>"
                f"      Copy"
                f"    </button>"
                f"  </div>"
                f"  {full_match}"
                f"</div>"
            )

        return pattern.sub(repl, html)

    def compute_stats(self, raw_text: str) -> Dict[str, str]:
        """Calculates word count, character count, and estimated reading time."""
        words = re.findall(r"\b\w+\b", raw_text)
        word_count = len(words)
        char_count = len(raw_text)
        reading_time_mins = max(1, round(word_count / 200))
        return {
            "words": f"{word_count:,}",
            "chars": f"{char_count:,}",
            "read_time": f"{reading_time_mins} min read",
        }

    def render(
        self, raw_md: str, file_path: str = ""
    ) -> Tuple[str, List[Tuple[int, str, str]], Dict[str, str]]:
        """Renders raw Markdown into complete HTML string with TOC and stats."""
        stats = self.compute_stats(raw_md)
        self.md_parser.reset()
        body_html = self.md_parser.convert(raw_md)
        body_html = self.postprocess_code_blocks(body_html)
        toc = []

        def flatten(tokens):
            for token in tokens:
                toc.append((token["level"], token["id"], html.unescape(token["name"])))
                flatten(token.get("children", []))

        flatten(self.md_parser.toc_tokens)
        if self.fragment:
            return body_html, toc, stats

        filename = os.path.basename(file_path) if file_path else "Markdown Document"
        filename = html.escape(filename)
        scroll_key = json.dumps("md_scroll_" + os.path.abspath(file_path)).replace(
            "<", "\\u003c"
        )
        complete_css = get_complete_css()
        math_script = ""
        if 'class="math"' in body_html:
            math_script = '<script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>'

        full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{filename}</title>
    <!-- MathJax for Math rendering -->
    <script>
    window.MathJax = {{
        tex: {{ inlineMath: [['$', '$'], ['\\\\(', '\\\\)']] }},
        svg: {{ fontCache: 'global' }}
    }};
    </script>
    {math_script}
    <style>
    {complete_css}
    </style>
</head>
<body>
    <div id="reading-progress" aria-hidden="true"></div>
    <div class="markdown-container">
        {body_html}
    </div>

    <script>
    // Store at most once after a scroll burst, using the actual document path.
    let scrollKey = {scroll_key};
    let scrollTimer;
    function saveScroll() {{
        try {{ localStorage.setItem(scrollKey, String(window.scrollY)); }} catch (_) {{}}
    }}
    function updateProgress() {{
        const range = document.documentElement.scrollHeight - window.innerHeight;
        document.getElementById('reading-progress').style.transform =
            'scaleX(' + (range > 0 ? window.scrollY / range : 0) + ')';
    }}
    function restoreScroll() {{
        try {{ window.scrollTo(0, Number(localStorage.getItem(scrollKey)) || 0); }} catch (_) {{}}
        updateProgress();
    }}
    window.addEventListener('scroll', () => {{
        clearTimeout(scrollTimer);
        scrollTimer = setTimeout(saveScroll, 150);
        requestAnimationFrame(updateProgress);
    }}, {{ passive: true }});
    window.addEventListener('pagehide', saveScroll);
    window.addEventListener('DOMContentLoaded', restoreScroll);
    window.addEventListener('resize', updateProgress);

    // The side panel keeps this page alive across file selections.
    let documentRevision = 0;
    function replaceDocument(source, baseURI, nextScrollKey, title, revision) {{
        const started = performance.now();
        saveScroll();
        clearTimeout(scrollTimer);
        const fragment = document.createElement('template');
        fragment.innerHTML = source;
        const parsedAt = performance.now();
        const content = document.querySelector('.markdown-container');
        if (window.MathJax && MathJax.typesetClear) MathJax.typesetClear([content]);
        let base = document.querySelector('base');
        if (!base) {{
            base = document.createElement('base');
            document.head.prepend(base);
        }}
        base.href = baseURI;
        document.title = title;
        content.replaceChildren(fragment.content);
        scrollKey = nextScrollKey;
        const insertedAt = performance.now();
        restoreScroll();
        const layoutAt = performance.now();
        documentRevision += 1;
        if (source.includes('class="math"')) {{
            if (window.MathJax && MathJax.typesetPromise) {{
                MathJax.typesetPromise([content]).catch(() => {{}});
            }} else if (!document.getElementById('mathjax-loader')) {{
                const script = document.createElement('script');
                script.id = 'mathjax-loader';
                script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js';
                script.async = true;
                script.onerror = () => script.remove();
                document.head.append(script);
            }}
        }}
        requestAnimationFrame(() => requestAnimationFrame(() => {{
            const handler = window.webkit?.messageHandlers?.markdownPreviewReady;
            if (handler) handler.postMessage(String(revision));
        }}));
        return JSON.stringify({{ parse: parsedAt - started, insert: insertedAt - parsedAt, layout: layoutAt - insertedAt, total: performance.now() - started }});
    }}

    // Load local font faces before the first selection, without network access.
    if (document.fonts) {{
        Promise.all([
            document.fonts.load('16px "Preview Sans"'),
            document.fonts.load('700 16px "Preview Sans"'),
            document.fonts.load('italic 16px "Preview Sans"'),
            document.fonts.load('14px "Preview Mono"'),
            document.fonts.load('700 14px "Preview Mono"'),
            document.fonts.load('16px "Preview Emoji"', '📑⚡🧭🔄🛠️'),
        ]).catch(() => {{}});
    }}

    // Code snippet copy handler
    function copySnippet(btn) {{
        const wrapper = btn.closest('.code-block-wrapper');
        const pre = wrapper.querySelector('pre');
        const text = pre.innerText;

        const setCopied = () => {{
            btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M13.78 4.22a.75.75 0 0 1 0 1.06l-7.25 7.25a.75.75 0 0 1-1.06 0L2.22 9.28a.751.751 0 0 1 .018-1.042.751.751 0 0 1 1.042-.018L6 10.94l6.72-6.72a.75.75 0 0 1 1.06 0Z"></path></svg> Copied!';
            btn.classList.add('copied');
            setTimeout(() => {{
                btn.innerHTML = '<svg width="12" height="12" viewBox="0 0 16 16" fill="currentColor"><path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 0 1 0 1.5h-1.5a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-1.5a.75.75 0 0 1 1.5 0v1.5A1.75 1.75 0 0 1 9.25 16h-7.5A1.75 1.75 0 0 1 0 14.25Z"></path><path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0 1 14.25 11h-7.5A1.75 1.75 0 0 1 5 9.25Zm1.75-.25a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-7.5a.25.25 0 0 0-.25-.25Z"></path></svg> Copy';
                btn.classList.remove('copied');
            }}, 2000);
        }};

        if (navigator.clipboard && navigator.clipboard.writeText) {{
            navigator.clipboard.writeText(text).then(setCopied).catch(fallbackCopy);
        }} else {{
            fallbackCopy();
        }}

        function fallbackCopy() {{
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            const copied = document.execCommand('copy');
            document.body.removeChild(ta);
            if (copied) setCopied();
            else btn.textContent = 'Select text to copy';
        }}
    }}

    // Theme switching API callable from GTK
    function setTheme(theme) {{
        const html = document.documentElement;
        html.classList.remove('light', 'dark');
        if (theme === 'dark') {{
            html.classList.add('dark');
        }} else if (theme === 'light') {{
            html.classList.add('light');
        }}
    }}

    function scrollToHeader(id) {{
        const el = document.getElementById(id);
        if (el) {{
            el.scrollIntoView({{ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' }});
        }}
    }}
    </script>
</body>
</html>
"""
        return full_html, toc, stats
