"""Renderer and file-integrity regressions; no desktop session required."""

import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "viewer"))

from documents import save_document
from renderer import MarkdownRenderer


class RendererTests(unittest.TestCase):
    def setUp(self):
        self.renderer = MarkdownRenderer()

    def render(self, text, path="/tmp/document.md"):
        return self.renderer.render(text, path)

    def test_formatted_and_duplicate_headings(self):
        _, toc, _ = self.render(
            "# Hello **world**\n\n## `code` & stuff\n\n# Hello **world**"
        )
        self.assertEqual(
            toc,
            [
                (1, "hello-world", "Hello world"),
                (2, "code-stuff", "code & stuff"),
                (1, "hello-world_1", "Hello world"),
            ],
        )

    def test_parser_state_resets(self):
        self.render("# Old")
        _, toc, _ = self.render("# New")
        self.assertEqual(toc, [(1, "new", "New")])

    def test_alerts_render_inline_markdown(self):
        for kind in ("NOTE", "TIP", "IMPORTANT", "WARNING", "CAUTION"):
            with self.subTest(kind=kind):
                html, _, _ = self.render(f"> [!{kind}]\n> **Important** text\n")
                self.assertIn(f"markdown-alert-{kind.lower()}", html)
                self.assertIn("<strong>Important</strong>", html)

    def test_fenced_examples_remain_literal(self):
        html, _, _ = self.render("```text\n- [x] example\n> [!NOTE]\n> literal\n```")
        body = html.split('<div class="markdown-container">')[1].split("<script>")[0]
        self.assertNotIn("<input", body)
        self.assertNotIn('<div class="markdown-alert', body)
        self.assertIn("- [x] example", body)

    def test_checklists_support_bullets_and_ordered_lists(self):
        html, _, _ = self.render(
            "- [x] Done\n- [ ] Open\n\n1. [X] Ordered\n2. [ ] Next"
        )
        self.assertEqual(html.count('<input aria-label="Task status"'), 4)
        self.assertEqual(html.count('checked="checked"'), 2)

    def test_code_language_and_copy_controls(self):
        html, _, _ = self.render("```python\nprint(42)\n```")
        self.assertIn('<span class="code-lang">python</span>', html)
        self.assertIn('onclick="copySnippet(this)"', html)
        self.assertIn('<span class="nb">print</span>', html)

    def test_plain_code_does_not_guess_language(self):
        html, _, _ = self.render("```\nplain words\n```")
        self.assertIn('class="codehilite language-text"', html)

    def test_math_download_only_when_needed(self):
        self.assertNotIn("<script async src=", self.render("# Plain")[0])
        self.assertIn("<script async src=", self.render("$x^2$")[0])

    def test_math_delimiters_survive_markdown(self):
        text = r"Inline \(x_1 + y_2\) and $a_b$ and `price $5$`."
        html, _, _ = self.render(text)
        self.assertIn(r'<span class="math">\(x_1 + y_2\)</span>', html)
        self.assertIn('<span class="math">$a_b$</span>', html)
        self.assertIn("<code>price $5$</code>", html)

    def test_indented_math_example_remains_code(self):
        html, _, _ = self.render('    cost = "$x$"\n')
        self.assertNotIn('<span class="math">', html)
        self.assertIn("$x$", html)

    def test_title_is_escaped(self):
        html, _, _ = self.render("hello", "/tmp/<script>.md")
        self.assertIn("<title>&lt;script&gt;.md</title>", html)

    def test_scroll_keys_distinguish_siblings(self):
        first = self.render("hello", "/tmp/one.md")[0]
        second = self.render("hello", "/tmp/two.md")[0]
        self.assertIn("md_scroll_/tmp/one.md", first)
        self.assertIn("md_scroll_/tmp/two.md", second)

    def test_tables_and_reading_stats(self):
        html, _, stats = self.render("| A | B |\n| --- | --- |\n| 1 | 2 |")
        self.assertIn("<table>", html)
        self.assertEqual(stats["words"], "4")
        self.assertEqual(stats["read_time"], "1 min read")


class DocumentTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "document.md"
        self.path.write_text("original", encoding="utf-8")

    def test_atomic_save_preserves_permissions(self):
        self.path.chmod(0o640)
        save_document(str(self.path), "updated", "original")
        self.assertEqual(self.path.read_text(), "updated")
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o640)
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_external_change_is_not_overwritten(self):
        self.path.write_text("external")
        with self.assertRaises(OSError):
            save_document(str(self.path), "editor", "original")
        self.assertEqual(self.path.read_text(), "external")

    def test_symlink_is_preserved(self):
        link = self.path.parent / "linked.md"
        link.symlink_to(self.path)
        save_document(str(link), "updated", "original")
        self.assertTrue(link.is_symlink())
        self.assertEqual(self.path.read_text(), "updated")

    def test_missing_file_is_not_recreated_silently(self):
        self.path.unlink()
        with self.assertRaises(FileNotFoundError):
            save_document(str(self.path), "updated", "original")


if __name__ == "__main__":
    unittest.main()
