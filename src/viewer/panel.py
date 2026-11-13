"""Markdown Side Panel for Nautilus File Explorer.
Embeds a horizontally draggable and stretchable preview pane into the Nautilus window,
with both Rendered Preview Mode and In-App GtkSourceView Editor Mode.
"""

import os
import sys
import shutil
import subprocess

# Ensure WebKitGTK runs cleanly in Ubuntu 24.04
os.environ["WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS"] = "1"

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
gi.require_version("GtkSource", "5")
from gi.repository import Gtk, Gdk, GLib, Gio, Adw, WebKit, GtkSource

from renderer import MarkdownRenderer

MARKDOWN_EXTENSIONS = {
    ".md", ".markdown", ".mdown", ".mkd", ".mdwn", ".mdx", ".rmd"
}


def launch_external_editor(file_path: str):
    """Explicitly launches an external text/code editor (never re-launches the previewer)."""
    code_bin = shutil.which("code") or ("/snap/bin/code" if os.path.exists("/snap/bin/code") else None)
    if code_bin:
        subprocess.Popen([code_bin, file_path], start_new_session=True)
        return

    gnome_editor = shutil.which("gnome-text-editor")
    if gnome_editor:
        subprocess.Popen([gnome_editor, file_path], start_new_session=True)
        return

    gedit = shutil.which("gedit")
    if gedit:
        subprocess.Popen([gedit, file_path], start_new_session=True)
        return

    app_info = Gio.AppInfo.get_default_for_type("text/plain", False)
    if app_info and app_info.get_id() != "io.github.markdown_previewer.desktop":
        app_info.launch_uris(["file://" + file_path], None)
    else:
        subprocess.Popen(["x-terminal-emulator", "-e", f"nano '{file_path}'"], start_new_session=True)


class MarkdownSidePanel(Gtk.Box):
    def __init__(self, on_close_callback=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_size_request(280, -1)
        self.add_css_class("background")
        
        self.on_close_callback = on_close_callback
        self.current_file_path = None
        self.current_mode = "preview"  # 'preview' or 'editor'
        self.renderer = MarkdownRenderer()
        self.file_monitor = None
        self.reload_timeout_id = 0
        self.theme_mode = "auto"
        self.zoom_level = 1.0

        self.setup_ui()

    def setup_ui(self):
        # Register local icons directory
        try:
            display = Gdk.Display.get_default()
            if display:
                theme = Gtk.IconTheme.get_for_display(display)
                icon_dir = os.path.expanduser("~/.local/share/icons/hicolor/scalable/actions")
                if icon_dir not in theme.get_search_path():
                    theme.add_search_path(icon_dir)
        except Exception:
            pass

        # 1. Header Toolbar
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.header_box.set_margin_top(6)
        self.header_box.set_margin_bottom(6)
        self.header_box.set_margin_start(10)
        self.header_box.set_margin_end(10)

        # File Icon & Title Label
        icon = Gtk.Image.new_from_icon_name("text-markdown-symbolic")
        self.header_box.append(icon)

        self.title_lbl = Gtk.Label(label="Markdown Preview", xalign=0, hexpand=True)
        self.title_lbl.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        self.title_lbl.add_css_class("heading")
        self.header_box.append(self.title_lbl)

        # In-Panel Mode Switcher (Preview <-> Editor)
        self.btn_mode = Gtk.Button(
            icon_name="document-edit-symbolic",
            tooltip_text="Switch to Editor Mode (Ctrl+E)"
        )
        self.btn_mode.add_css_class("flat")
        self.btn_mode.connect("clicked", lambda _: self.toggle_mode())
        self.header_box.append(self.btn_mode)

        # Save Button (Active in Editor Mode)
        self.btn_save = Gtk.Button(
            icon_name="document-save-symbolic",
            tooltip_text="Save Changes (Ctrl+S)"
        )
        self.btn_save.add_css_class("suggested-action")
        self.btn_save.set_visible(False)
        self.btn_save.set_sensitive(False)
        self.btn_save.connect("clicked", lambda _: self.save_file())
        self.header_box.append(self.btn_save)

        # External Editor Button (VS Code / GNOME Text Editor)
        btn_ext = Gtk.Button(
            icon_name="accessories-text-editor-symbolic",
            tooltip_text="Open in VS Code / External Editor"
        )
        btn_ext.add_css_class("flat")
        btn_ext.connect("clicked", self.on_ext_editor_clicked)
        self.header_box.append(btn_ext)

        # Standalone Window Button
        btn_popout = Gtk.Button(
            icon_name="window-new-symbolic",
            tooltip_text="Open in Full Previewer Window"
        )
        btn_popout.add_css_class("flat")
        btn_popout.connect("clicked", self.on_popout_clicked)
        self.header_box.append(btn_popout)

        # Refresh Button
        btn_reload = Gtk.Button(
            icon_name="view-refresh-symbolic",
            tooltip_text="Reload Preview"
        )
        btn_reload.add_css_class("flat")
        btn_reload.connect("clicked", lambda _: self.reload_current())
        self.header_box.append(btn_reload)

        # Close Panel Button
        btn_close = Gtk.Button(
            icon_name="window-close-symbolic",
            tooltip_text="Close Preview Panel"
        )
        btn_close.add_css_class("flat")
        btn_close.connect("clicked", self.on_close_clicked)
        self.header_box.append(btn_close)

        self.append(self.header_box)

        # Separator line under header
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.append(sep)

        # 2. Stack (Empty State vs WebKit Preview vs GtkSourceView Editor)
        self.stack = Gtk.Stack(vexpand=True, hexpand=True)
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        # Page 1: Empty State
        self.status_page = Adw.StatusPage()
        self.status_page.set_icon_name("text-markdown-symbolic")
        self.status_page.set_title("Select a Markdown File")
        self.status_page.set_description("Select any .md file in the explorer to preview it here.")
        self.stack.add_named(self.status_page, "empty")

        # Page 2: WebKit Preview
        self.webview = WebKit.WebView(vexpand=True, hexpand=True)
        settings = self.webview.get_settings()
        settings.set_enable_developer_extras(False)
        settings.set_javascript_can_access_clipboard(True)
        self.webview.connect("decide-policy", self.on_decide_policy)
        self.stack.add_named(self.webview, "preview")

        # Page 3: In-Panel GtkSourceView Editor
        self.editor_scroll = Gtk.ScrolledWindow(vexpand=True, hexpand=True)
        self.editor_buffer = GtkSource.Buffer()
        lang = GtkSource.LanguageManager.get_default().get_language("markdown")
        if lang:
            self.editor_buffer.set_language(lang)

        self.editor_buffer.connect("modified-changed", self.on_buffer_modified_changed)

        self.source_view = GtkSource.View(buffer=self.editor_buffer)
        self.source_view.set_show_line_numbers(True)
        self.source_view.set_highlight_current_line(True)
        self.source_view.set_auto_indent(True)
        self.source_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.source_view.set_monospace(True)
        self.source_view.set_top_margin(8)
        self.source_view.set_bottom_margin(8)
        self.source_view.set_left_margin(12)
        self.source_view.set_right_margin(12)

        self.editor_scroll.set_child(self.source_view)
        self.stack.add_named(self.editor_scroll, "editor")

        self.append(self.stack)

        # Listen to system color scheme changes
        style_manager = Adw.StyleManager.get_default()
        style_manager.connect("notify::dark", self.on_system_theme_changed)
        self.update_editor_theme(style_manager.get_dark())

    def update_editor_theme(self, is_dark: bool):
        scheme_mgr = GtkSource.StyleSchemeManager.get_default()
        scheme_id = "Adwaita-dark" if is_dark else "Adwaita"
        scheme = scheme_mgr.get_scheme(scheme_id)
        if scheme:
            self.editor_buffer.set_style_scheme(scheme)

    def on_system_theme_changed(self, _style_manager, _pspec):
        if self.theme_mode == "auto":
            is_dark = Adw.StyleManager.get_default().get_dark()
            self.update_editor_theme(is_dark)
            target = "dark" if is_dark else "light"
            js = f"if (typeof setTheme === 'function') setTheme('{target}');"
            self.webview.evaluate_javascript(js, -1, None, None, None, None)

    def on_decide_policy(self, _webview, decision, decision_type):
        if decision_type == WebKit.PolicyDecisionType.NAVIGATION_ACTION:
            action = decision.get_navigation_action()
            uri = action.get_request().get_uri()
            if uri.startswith(("http://", "https://", "mailto:")):
                decision.ignore()
                Gtk.show_uri(self.get_root(), uri, Gdk.CURRENT_TIME)
                return True
        return False

    def on_close_clicked(self, _button):
        if self.on_close_callback:
            self.on_close_callback()
        else:
            self.set_visible(False)

    def on_ext_editor_clicked(self, _button):
        if self.current_file_path and os.path.exists(self.current_file_path):
            launch_external_editor(self.current_file_path)

    def on_popout_clicked(self, _button):
        if self.current_file_path and os.path.exists(self.current_file_path):
            bin_path = os.path.expanduser("~/.local/bin/markdown-preview")
            subprocess.Popen([bin_path, self.current_file_path], start_new_session=True)

    def toggle_mode(self):
        if not self.current_file_path:
            return

        if self.current_mode == "preview":
            # Switch to Editor
            self.current_mode = "editor"
            self.btn_mode.set_icon_name("text-markdown-symbolic")
            self.btn_mode.set_tooltip_text("Switch to Preview Mode (Ctrl+E)")
            self.btn_save.set_visible(True)

            try:
                with open(self.current_file_path, "r", encoding="utf-8", errors="replace") as f:
                    raw_text = f.read()
                self.editor_buffer.set_text(raw_text)
                self.editor_buffer.set_modified(False)
                self.btn_save.set_sensitive(False)
            except Exception as e:
                self.editor_buffer.set_text(f"Error loading file: {e}")

            self.stack.set_visible_child_name("editor")
            self.source_view.grab_focus()
        else:
            # Switch to Preview
            if self.editor_buffer.get_modified():
                self.save_file()

            self.current_mode = "preview"
            self.btn_mode.set_icon_name("document-edit-symbolic")
            self.btn_mode.set_tooltip_text("Switch to Editor Mode (Ctrl+E)")
            self.btn_save.set_visible(False)

            self.reload_current()
            self.stack.set_visible_child_name("preview")

    def on_buffer_modified_changed(self, buffer):
        modified = buffer.get_modified()
        self.btn_save.set_sensitive(modified)
        if modified and self.current_file_path:
            self.title_lbl.set_text(f"● {os.path.basename(self.current_file_path)}")
        elif self.current_file_path:
            self.title_lbl.set_text(os.path.basename(self.current_file_path))

    def save_file(self):
        if not self.current_file_path or not self.editor_buffer.get_modified():
            return

        start = self.editor_buffer.get_start_iter()
        end = self.editor_buffer.get_end_iter()
        text = self.editor_buffer.get_text(start, end, True)

        try:
            with open(self.current_file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.editor_buffer.set_modified(False)
            self.btn_save.set_sensitive(False)
            self.title_lbl.set_text(os.path.basename(self.current_file_path))
        except Exception as e:
            self.status_page.set_title("Error Saving")
            self.status_page.set_description(str(e))

    def set_file(self, file_path: str):
        """Called when selection in Nautilus changes."""
        if not file_path or not os.path.isfile(file_path):
            self.current_file_path = None
            self.status_page.set_title("Select a Markdown File")
            self.status_page.set_description("Select any .md file in the explorer to preview it here.")
            self.title_lbl.set_text("Markdown Preview")
            self.btn_mode.set_sensitive(False)
            self.btn_save.set_visible(False)
            self.stack.set_visible_child_name("empty")
            self._cleanup_monitor()
            return

        _, ext = os.path.splitext(file_path.lower())
        if ext not in MARKDOWN_EXTENSIONS:
            self.current_file_path = None
            self.status_page.set_title("Not a Markdown File")
            self.status_page.set_description(f"'{os.path.basename(file_path)}' is not a Markdown document.")
            self.title_lbl.set_text("Markdown Preview")
            self.btn_mode.set_sensitive(False)
            self.btn_save.set_visible(False)
            self.stack.set_visible_child_name("empty")
            self._cleanup_monitor()
            return

        if self.current_file_path == file_path:
            return  # Already showing this file

        self.current_file_path = file_path
        self.btn_mode.set_sensitive(True)
        self.title_lbl.set_text(os.path.basename(file_path))

        if self.current_mode == "editor":
            try:
                with open(self.current_file_path, "r", encoding="utf-8", errors="replace") as f:
                    raw_text = f.read()
                self.editor_buffer.set_text(raw_text)
                self.editor_buffer.set_modified(False)
                self.btn_save.set_sensitive(False)
            except Exception:
                pass
        else:
            self.reload_current()

        self.setup_file_monitor()

    def reload_current(self):
        if not self.current_file_path or not os.path.exists(self.current_file_path):
            return

        try:
            with open(self.current_file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            html_output, _toc, _stats = self.renderer.render(content, self.current_file_path)
            base_uri = "file://" + os.path.dirname(self.current_file_path) + "/"
            self.webview.load_html(html_output, base_uri)
            self.stack.set_visible_child_name("preview")

            # Apply dark/light theme
            is_dark = Adw.StyleManager.get_default().get_dark()
            target = "dark" if is_dark else "light"
            js = f"if (typeof setTheme === 'function') setTheme('{target}');"
            self.webview.evaluate_javascript(js, -1, None, None, None, None)
        except Exception as e:
            self.status_page.set_title("Error Rendering")
            self.status_page.set_description(str(e))
            self.stack.set_visible_child_name("empty")

    def setup_file_monitor(self):
        self._cleanup_monitor()
        if self.current_file_path:
            gfile = Gio.File.new_for_path(self.current_file_path)
            self.file_monitor = gfile.monitor_file(Gio.FileMonitorFlags.NONE, None)
            self.file_monitor.connect("changed", self._on_file_changed)

    def _cleanup_monitor(self):
        if self.file_monitor:
            self.file_monitor.cancel()
            self.file_monitor = None

    def _on_file_changed(self, _monitor, _file, _other, event_type):
        if event_type in (Gio.FileMonitorEvent.CHANGES_DONE_HINT, Gio.FileMonitorEvent.CHANGED):
            if self.current_mode == "preview":
                if self.reload_timeout_id != 0:
                    GLib.source_remove(self.reload_timeout_id)
                self.reload_timeout_id = GLib.timeout_add(250, self._debounced_reload)

    def _debounced_reload(self):
        self.reload_timeout_id = 0
        self.reload_current()
        return False
