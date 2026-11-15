"""Opt-in integration checks against real GTK, GtkSourceView and WebKit.

Run with RUN_DESKTOP_TESTS=1 /usr/bin/python3 -m unittest discover -s tests.
Requires a display server and the application's system dependencies.
"""

import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "viewer"))

ENABLED = os.environ.get("RUN_DESKTOP_TESTS") == "1"
if ENABLED:
    from viewer import MarkdownViewerApp, MarkdownViewerWindow, GLib, Gdk
    from panel import MarkdownSidePanel
    from loading import PreviewLoader


@unittest.skipUnless(ENABLED, "Set RUN_DESKTOP_TESTS=1 to exercise GTK/WebKit")
class DesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = MarkdownViewerApp()
        cls.app.register(None)

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "document #1.md"
        self.path.write_text(
            "# Hello **world**\n\nsearchable words\n\n```python\nprint(42)\n```"
        )
        self.window = MarkdownViewerWindow(self.app, str(self.path))
        self.window.present()
        self.addCleanup(self.close_window)
        self.wait_for(
            lambda: self.window._last_html is not None
            and not self.window.webview.is_loading()
        )

    def close_window(self):
        self.window.editor_buffer.set_modified(False)
        self.window.close()

    def wait_for(self, predicate, timeout=10):
        deadline = time.monotonic() + timeout
        context = GLib.MainContext.default()
        while time.monotonic() < deadline:
            while context.pending():
                context.iteration(False)
            if predicate():
                return
            time.sleep(0.01)
        self.fail("Timed out waiting for GTK/WebKit state")

    def javascript(self, script, webview=None):
        result = []

        def complete(view, task, _data):
            try:
                result.append((view.evaluate_javascript_finish(task).to_string(), None))
            except Exception as error:
                result.append((None, error))

        (webview or self.window.webview).evaluate_javascript(
            script, -1, None, None, None, complete, None
        )
        self.wait_for(lambda: bool(result))
        if result[0][1]:
            raise result[0][1]
        return result[0][0]

    def test_preview_dom_theme_and_zoom(self):
        self.assertEqual(
            self.javascript('document.querySelector("h1").textContent'), "Hello world"
        )
        self.assertEqual(len(self.window.toc_items), 1)
        self.window.on_cycle_theme(None)
        self.assertEqual(self.javascript("document.documentElement.className"), "dark")
        self.window.on_cycle_theme(None)
        self.assertEqual(self.javascript("document.documentElement.className"), "light")
        self.window.adjust_zoom(0.1)
        self.assertAlmostEqual(self.window.webview.get_zoom_level(), 1.1)
        self.window.reset_zoom()
        self.assertEqual(self.window.webview.get_zoom_level(), 1)

    def test_editor_save_and_return_to_preview(self):
        self.window.toggle_mode()
        self.assertEqual(self.window.stack.get_visible_child_name(), "editor")
        self.window.editor_buffer.set_text("# Updated")
        self.assertTrue(self.window.save_file())
        self.assertEqual(self.path.read_text(), "# Updated")
        self.window.toggle_mode()
        self.wait_for(lambda: self.window.toc_items == [(1, "updated", "Updated")])
        self.assertEqual(self.window.stack.get_visible_child_name(), "preview")

    def test_save_conflict_keeps_editor_and_disk(self):
        messages = []
        self.window.show_error = lambda title, message: messages.append(message)
        self.window.toggle_mode()
        self.window.editor_buffer.set_text("my edits")
        self.path.write_text("external edits")
        self.window.toggle_mode()
        self.assertEqual(self.window.current_mode, "editor")
        self.assertTrue(self.window.editor_buffer.get_modified())
        self.assertEqual(self.path.read_text(), "external edits")
        self.assertTrue(messages)

    def test_search_and_escape(self):
        self.window.search_btn.set_active(True)
        self.window.search_entry.set_text("searchable")
        self.window.on_search_text_changed(self.window.search_entry)
        self.wait_for(lambda: self.window.lbl_search_count.get_text() == "1 matches")
        self.assertTrue(self.window.on_key_pressed(None, Gdk.KEY_Escape, 0, 0))
        self.assertFalse(self.window.search_bar.get_search_mode())

    def test_atomic_external_save_and_f5(self):
        replacement = self.path.with_suffix(".tmp")
        replacement.write_text("# Atomic")
        replacement.replace(self.path)
        self.wait_for(lambda: self.window.toc_items == [(1, "atomic", "Atomic")])
        self.assertTrue(self.window.on_key_pressed(None, Gdk.KEY_F5, 0, 0))

    def test_panel_selection_save_and_keyboard(self):
        panel = MarkdownSidePanel()
        self.addCleanup(panel.close_resources)
        panel.set_file(str(self.path))
        self.wait_for(lambda: panel._last_html is not None)
        panel.on_key_pressed(None, Gdk.KEY_e, 0, Gdk.ModifierType.CONTROL_MASK)
        panel.editor_buffer.set_text("# Saved selection")
        second = self.path.parent / "second.md"
        second.write_text("# Second")
        panel.set_file(str(second))
        self.assertEqual(self.path.read_text(), "# Saved selection")
        self.wait_for(
            lambda: panel._last_html is not None
            and '<h1 id="second">' in panel._last_html
        )
        panel.set_file(None)
        self.assertEqual(panel.stack.get_visible_child_name(), "empty")
        panel.set_file(str(self.path))
        self.wait_for(lambda: panel.stack.get_visible_child_name() == "preview")

    def test_relative_image_and_code_copy(self):
        import base64

        image = self.path.parent / "pixel.png"
        image.write_bytes(
            base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aXioAAAAASUVORK5CYII="
            )
        )
        self.path.write_text("# Image\n\n![pixel](pixel.png)\n\n```text\ncopy me\n```")
        self.window.load_and_render()
        self.wait_for(
            lambda: self.window.toc_items == [(1, "image", "Image")]
            and not self.window.webview.is_loading()
        )
        self.assertEqual(
            self.javascript('document.querySelector("img").naturalWidth'), "1"
        )
        self.javascript('document.querySelector(".copy-button").click(); "clicked"')
        self.wait_for(
            lambda: self.javascript(
                'document.querySelector(".copy-button").textContent'
            ).strip()
            == "Copied!"
        )

    def test_scroll_restoration_and_reading_progress(self):
        self.path.write_text("# Long\n\n" + "paragraph\n\n" * 150)
        self.window.load_and_render()
        self.wait_for(
            lambda: self.window.toc_items == [(1, "long", "Long")]
            and not self.window.webview.is_loading()
        )
        self.javascript(
            'window.scrollTo(0, 600); saveScroll(); updateProgress(); "scrolled"'
        )
        self.assertGreater(float(self.javascript("window.scrollY")), 500)
        self.assertNotEqual(
            self.javascript(
                'document.getElementById("reading-progress").style.transform'
            ),
            "scaleX(0)",
        )
        self.path.write_text(self.path.read_text() + "End")
        self.window.load_and_render()
        self.wait_for(
            lambda: "<p>End</p>" in (self.window._last_html or "")
            and not self.window.webview.is_loading()
        )
        self.assertGreater(float(self.javascript("window.scrollY")), 500)

    def test_rich_preview_is_only_mode_and_loader_recovers(self):
        panel = MarkdownSidePanel()
        self.addCleanup(panel.close_resources)
        self.assertIsNotNone(panel.webview)
        self.assertFalse(hasattr(panel, "btn_rich"))
        self.assertFalse(hasattr(panel, "native_preview"))
        callbacks = []
        panel.loader.request = lambda path, callback: callbacks.append(callback)
        panel.set_file(str(self.path))
        self.wait_for(lambda: panel.loading_box.get_visible())
        self.assertTrue(panel.loading_spinner.get_spinning())
        callbacks[-1](None, "Cannot read document")
        self.assertFalse(panel.loading_box.get_visible())
        self.assertEqual(panel.stack.get_visible_child_name(), "empty")
        panel._preview_failed("Browser stopped")
        self.assertFalse(panel.loading_spinner.get_spinning())

    def test_rich_panel_frame_clears_loader_and_offscreen_search_works(self):
        from gi.repository import Gtk

        panel = MarkdownSidePanel()
        host = Gtk.Window(default_width=520, default_height=700)
        host.set_child(panel)
        self.addCleanup(host.destroy)
        self.addCleanup(panel.close_resources)
        host.present()
        self.path.write_text(
            "# Start\n\n"
            + "Paragraph text.\n\n" * 120
            + "## Destination\n\nUniqueTarget"
        )
        panel.set_file(str(self.path))
        self.wait_for(lambda: panel.preview.applied_revision == 1)
        self.wait_for(
            lambda: panel._loading_delay == 0 and not panel.loading_box.get_visible()
        )
        matches = []
        finder = panel.webview.get_find_controller()
        finder.connect("found-text", lambda _finder, count: matches.append(count))
        from gi.repository import WebKit

        finder.search("UniqueTarget", WebKit.FindOptions.WRAP_AROUND, 100)
        self.wait_for(lambda: bool(matches))
        self.assertGreater(matches[-1], 0)
        finder.search_finish()
        self.javascript(
            "document.getElementById('destination').scrollIntoView(); 'ok'",
            panel.webview,
        )
        self.wait_for(
            lambda: float(
                self.javascript(
                    "document.getElementById('destination').getBoundingClientRect().top",
                    panel.webview,
                )
            )
            < 700
        )
        self.assertGreater(float(self.javascript("window.scrollY", panel.webview)), 0)

    def test_persistent_panel_updates_without_navigation(self):
        from gi.repository import WebKit

        panel = MarkdownSidePanel()
        self.addCleanup(panel.close_resources)
        self.wait_for(lambda: panel.preview._ready)
        navigations = []
        panel.webview.connect(
            "load-changed", lambda _view, event: navigations.append(event)
        )
        first = self.path.parent / "first.md"
        second = self.path.parent / "second.md"
        first.write_text("# First\n\n```python\nprint(1)\n```")
        second.write_text("# Second\n\n- [x] Complete")
        for index, path in enumerate((first, second, first), start=1):
            panel.set_file(str(path))
            self.wait_for(lambda: panel.preview.applied_revision == index)
            self.assertEqual(
                self.javascript(
                    'document.querySelector("h1").textContent', panel.webview
                ),
                path.stem.title(),
            )
            self.assertEqual(
                self.javascript("document.baseURI", panel.webview),
                path.parent.as_uri() + "/",
            )
        self.assertNotIn(WebKit.LoadEvent.STARTED, navigations)
        self.assertEqual(len(panel.loader._cache), 2)
        first.write_text("# Changed")
        panel.reload_current()
        self.wait_for(lambda: panel.preview.applied_revision == 4)
        self.assertEqual(
            self.javascript('document.querySelector("h1").textContent', panel.webview),
            "Changed",
        )

    def test_latest_render_wins_and_errors_arrive(self):
        loader = PreviewLoader()
        self.addCleanup(loader.close)
        results = []
        for number in range(20):
            path = self.path.parent / f"{number}.md"
            path.write_text(f"# Document {number}")
            loader.request(
                str(path), lambda value, error: results.append((value, error))
            )
        self.wait_for(lambda: bool(results))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][0][1], [(1, "document-19", "Document 19")])
        loader.request(
            str(self.path.parent / "missing.md"),
            lambda value, error: results.append((value, error)),
        )
        self.wait_for(lambda: len(results) == 2)
        self.assertIsNotNone(results[-1][1])


if __name__ == "__main__":
    unittest.main()
