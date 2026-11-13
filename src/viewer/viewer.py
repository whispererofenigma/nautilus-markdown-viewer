#!/usr/bin/env python3
"""Main GTK4 + Libadwaita Markdown Viewer and Editor Window.
Provides rich interactive features:
1. Preview Mode: Rendered HTML with TOC, In-Page Search, Dark/Light Themes, Zoom controls.
2. Edit Mode: Built-in Markdown code editor with GtkSourceView syntax highlighting,
   line numbers, auto-indent, and Save (Ctrl+S).
3. External Editor Launcher: Directly opens in VS Code or GNOME Text Editor without duplicate windows.
"""

import os
import sys
import shutil
import subprocess

# Ensure WebKitGTK sandbox doesn't conflict with Ubuntu 24.04 unprivileged userns restriction
os.environ["WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS"] = "1"

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
gi.require_version("GtkSource", "5")
from gi.repository import Gtk, Gdk, GLib, Gio, Adw, WebKit, GtkSource

from renderer import MarkdownRenderer


def launch_external_editor(file_path: str):
    """Explicitly launches an external text/code editor (never re-launches the previewer)."""
    # 1. VS Code
    code_bin = shutil.which("code") or ("/snap/bin/code" if os.path.exists("/snap/bin/code") else None)
    if code_bin:
        subprocess.Popen([code_bin, file_path], start_new_session=True)
        return

    # 2. GNOME Text Editor
    gnome_editor = shutil.which("gnome-text-editor")
    if gnome_editor:
        subprocess.Popen([gnome_editor, file_path], start_new_session=True)
        return

    # 3. Gedit
    gedit = shutil.which("gedit")
    if gedit:
        subprocess.Popen([gedit, file_path], start_new_session=True)
        return

    # 4. Fallback to generic text/plain handler if different from previewer
    app_info = Gio.AppInfo.get_default_for_type("text/plain", False)
    if app_info and app_info.get_id() != "io.github.markdown_previewer.desktop":
        app_info.launch_uris(["file://" + file_path], None)
    else:
        # Default to nano in a terminal if nothing else exists
        subprocess.Popen(["x-terminal-emulator", "-e", f"nano '{file_path}'"], start_new_session=True)


class MarkdownViewerWindow(Adw.ApplicationWindow):
    def __init__(self, app: Adw.Application, file_path: str):
        super().__init__(application=app)
        self.file_path = os.path.abspath(file_path)
        self.renderer = MarkdownRenderer()
        self.zoom_level = 1.0
        self.theme_mode = "auto"  # 'auto', 'light', 'dark'
        self.current_mode = "preview"  # 'preview' or 'editor'
        self.file_monitor = None
        self.reload_timeout_id = 0
        self.toc_items = []
        self.stats = {}

        self.setup_ui()
        self.setup_keybindings()
        self.setup_file_monitor()
        self.load_and_render()

    def setup_ui(self):
        self.set_default_size(980, 780)
        self.set_size_request(520, 420)

        # Main vertical box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(main_box)

        # Header Bar
        self.header = Adw.HeaderBar()
        main_box.append(self.header)

        # Window Title
        filename = os.path.basename(self.file_path)
        dir_name = os.path.dirname(self.file_path)
        home = os.path.expanduser("~")
        if dir_name.startswith(home):
            dir_name = "~" + dir_name[len(home):]

        self.original_subtitle = dir_name
        self.win_title = Adw.WindowTitle(title=filename, subtitle=dir_name)
        self.header.set_title_widget(self.win_title)

        # ==========================================================
        # Left (Start) Controls
        # ==========================================================

        # Table of Contents Button & Popover
        self.toc_button = Gtk.MenuButton(
            icon_name="view-list-bullet-symbolic",
            tooltip_text="Table of Contents"
        )
        self.toc_popover = Gtk.Popover()
        self.toc_scroll = Gtk.ScrolledWindow(
            hscrollbar_policy=Gtk.PolicyType.NEVER,
            vscrollbar_policy=Gtk.PolicyType.AUTOMATIC
        )
        self.toc_scroll.set_size_request(280, 360)
        self.toc_listbox = Gtk.ListBox()
        self.toc_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.toc_listbox.add_css_class("navigation-sidebar")
        self.toc_scroll.set_child(self.toc_listbox)
        self.toc_popover.set_child(self.toc_scroll)
        self.toc_button.set_popover(self.toc_popover)
        self.header.pack_start(self.toc_button)

        # Reading Stats Button & Popover
        self.stats_button = Gtk.MenuButton(
            icon_name="dialog-information-symbolic",
            tooltip_text="Document Statistics"
        )
        self.stats_popover = Gtk.Popover()
        self.stats_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.stats_box.set_margin_top(12)
        self.stats_box.set_margin_bottom(12)
        self.stats_box.set_margin_start(16)
        self.stats_box.set_margin_end(16)

        self.lbl_stats_words = Gtk.Label(xalign=0)
        self.lbl_stats_chars = Gtk.Label(xalign=0)
        self.lbl_stats_time = Gtk.Label(xalign=0)
        for lbl in (self.lbl_stats_words, self.lbl_stats_chars, self.lbl_stats_time):
            self.stats_box.append(lbl)

        self.stats_popover.set_child(self.stats_box)
        self.stats_button.set_popover(self.stats_popover)
        self.header.pack_start(self.stats_button)

        # ==========================================================
        # Mode Switcher & Save Button
        # ==========================================================

        # Mode Toggle Button (Switches between Preview and Edit Mode)
        self.mode_btn = Gtk.Button(
            icon_name="document-edit-symbolic",
            tooltip_text="Switch to Editor Mode (Ctrl+E)"
        )
        self.mode_btn.connect("clicked", lambda _: self.toggle_mode())
        self.header.pack_start(self.mode_btn)

        # Save Button (Active in Edit Mode)
        self.save_btn = Gtk.Button(
            icon_name="document-save-symbolic",
            tooltip_text="Save Changes (Ctrl+S)"
        )
        self.save_btn.add_css_class("suggested-action")
        self.save_btn.set_sensitive(False)
        self.save_btn.set_visible(False)
        self.save_btn.connect("clicked", lambda _: self.save_file())
        self.header.pack_start(self.save_btn)

        # ==========================================================
        # Right (End) Controls
        # ==========================================================

        # Search Toggle Button
        self.search_btn = Gtk.ToggleButton(
            icon_name="edit-find-symbolic",
            tooltip_text="Find in Document (Ctrl+F)"
        )
        self.search_btn.connect("toggled", self.on_search_toggle)
        self.header.pack_end(self.search_btn)

        # Theme Cycle Button (Auto -> Dark -> Light)
        self.theme_btn = Gtk.Button(
            icon_name="weather-clear-night-symbolic",
            tooltip_text="Toggle Theme (Auto / Dark / Light)"
        )
        self.theme_btn.connect("clicked", self.on_cycle_theme)
        self.header.pack_end(self.theme_btn)

        # External Editor Menu Button
        ext_menu_btn = Gtk.MenuButton(
            icon_name="view-more-symbolic",
            tooltip_text="More Options"
        )
        ext_popover = Gtk.Popover()
        ext_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        ext_box.set_margin_top(6)
        ext_box.set_margin_bottom(6)
        ext_box.set_margin_start(6)
        ext_box.set_margin_end(6)

        btn_open_code = Gtk.Button(label="Open in VS Code")
        btn_open_code.add_css_class("flat")
        btn_open_code.connect("clicked", lambda _: [ext_popover.popdown(), launch_external_editor(self.file_path)])
        ext_box.append(btn_open_code)

        btn_open_ext = Gtk.Button(label="Open in System Text Editor")
        btn_open_ext.add_css_class("flat")
        btn_open_ext.connect("clicked", lambda _: [
            ext_popover.popdown(),
            subprocess.Popen(["gnome-text-editor", self.file_path], start_new_session=True)
            if shutil.which("gnome-text-editor") else launch_external_editor(self.file_path)
        ])
        ext_box.append(btn_open_ext)

        ext_popover.set_child(ext_box)
        ext_menu_btn.set_popover(ext_popover)
        self.header.pack_end(ext_menu_btn)

        # Zoom Controls MenuButton
        zoom_btn = Gtk.MenuButton(
            icon_name="zoom-original-symbolic",
            tooltip_text="Zoom Controls"
        )
        zoom_popover = Gtk.Popover()
        zoom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        zoom_box.set_margin_top(6)
        zoom_box.set_margin_bottom(6)
        zoom_box.set_margin_start(6)
        zoom_box.set_margin_end(6)

        btn_zoom_out = Gtk.Button(icon_name="zoom-out-symbolic", tooltip_text="Zoom Out (Ctrl -)")
        btn_zoom_out.connect("clicked", lambda _: self.adjust_zoom(-0.1))
        btn_zoom_reset = Gtk.Button(label="100%", tooltip_text="Reset Zoom (Ctrl 0)")
        btn_zoom_reset.connect("clicked", lambda _: self.reset_zoom())
        btn_zoom_in = Gtk.Button(icon_name="zoom-in-symbolic", tooltip_text="Zoom In (Ctrl +)")
        btn_zoom_in.connect("clicked", lambda _: self.adjust_zoom(+0.1))

        zoom_box.append(btn_zoom_out)
        zoom_box.append(btn_zoom_reset)
        zoom_box.append(btn_zoom_in)
        zoom_popover.set_child(zoom_box)
        zoom_btn.set_popover(zoom_popover)
        self.header.pack_end(zoom_btn)

        # Reload Button
        self.reload_btn = Gtk.Button(
            icon_name="view-refresh-symbolic",
            tooltip_text="Reload (Ctrl+R / F5)"
        )
        self.reload_btn.connect("clicked", lambda _: self.load_and_render())
        self.header.pack_end(self.reload_btn)

        # ==========================================================
        # Search Bar
        # ==========================================================
        self.search_bar = Gtk.SearchBar()
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        search_box.set_margin_top(4)
        search_box.set_margin_bottom(4)
        search_box.set_margin_start(8)
        search_box.set_margin_end(8)

        self.search_entry = Gtk.SearchEntry(hexpand=True)
        self.search_entry.connect("search-changed", self.on_search_text_changed)
        self.search_entry.connect("activate", lambda _: self.find_next())
        search_box.append(self.search_entry)

        self.lbl_search_count = Gtk.Label(label="", xalign=0)
        self.lbl_search_count.add_css_class("dim-label")
        search_box.append(self.lbl_search_count)

        btn_find_prev = Gtk.Button(icon_name="go-up-symbolic", tooltip_text="Previous Match (Shift+Enter)")
        btn_find_prev.connect("clicked", lambda _: self.find_prev())
        btn_find_next = Gtk.Button(icon_name="go-down-symbolic", tooltip_text="Next Match (Enter)")
        btn_find_next.connect("clicked", lambda _: self.find_next())
        search_box.append(btn_find_prev)
        search_box.append(btn_find_next)

        self.search_bar.set_child(search_box)
        self.search_bar.connect_entry(self.search_entry)
        main_box.append(self.search_bar)

        # ==========================================================
        # Main View Stack (Preview Mode vs. Editor Mode)
        # ==========================================================
        self.stack = Gtk.Stack(vexpand=True, hexpand=True)
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)

        # 1. Preview Page (WebKitGTK)
        self.webview = WebKit.WebView(vexpand=True, hexpand=True)
        settings = self.webview.get_settings()
        settings.set_enable_developer_extras(False)
        settings.set_javascript_can_access_clipboard(True)

        self.find_controller = self.webview.get_find_controller()
        self.find_controller.connect("counted-matches", self.on_find_counted_matches)
        self.find_controller.connect("found-text", self.on_find_found_text)
        self.find_controller.connect("failed-to-find-text", self.on_find_failed)
        self.webview.connect("decide-policy", self.on_decide_policy)
        self.stack.add_named(self.webview, "preview")

        # 2. Editor Page (GtkSourceView)
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
        self.source_view.set_top_margin(12)
        self.source_view.set_bottom_margin(12)
        self.source_view.set_left_margin(16)
        self.source_view.set_right_margin(16)

        self.editor_scroll.set_child(self.source_view)
        self.stack.add_named(self.editor_scroll, "editor")

        main_box.append(self.stack)

        # Style & Theme Management
        style_manager = Adw.StyleManager.get_default()
        style_manager.connect("notify::dark", self.on_system_theme_changed)
        self.update_editor_theme(style_manager.get_dark())

    def update_editor_theme(self, is_dark: bool):
        scheme_mgr = GtkSource.StyleSchemeManager.get_default()
        scheme_id = "Adwaita-dark" if is_dark else "Adwaita"
        scheme = scheme_mgr.get_scheme(scheme_id)
        if scheme:
            self.editor_buffer.set_style_scheme(scheme)

    def setup_keybindings(self):
        controller = Gtk.EventControllerKey()
        controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(controller)

    def on_key_pressed(self, controller, keyval, keycode, state):
        ctrl = state & Gdk.ModifierType.CONTROL_MASK

        if keyval == Gdk.KEY_Escape:
            if self.search_bar.get_search_mode():
                self.search_bar.set_search_mode(False)
                self.search_btn.set_active(False)
                self.find_controller.search_finish()
                return True

        if ctrl:
            if keyval in (Gdk.KEY_e, Gdk.KEY_E):
                self.toggle_mode()
                return True
            elif keyval in (Gdk.KEY_s, Gdk.KEY_S):
                self.save_file()
                return True
            elif keyval in (Gdk.KEY_f, Gdk.KEY_F):
                self.search_btn.set_active(not self.search_btn.get_active())
                return True
            elif keyval in (Gdk.KEY_r, Gdk.KEY_R) or keyval == Gdk.KEY_F5:
                self.load_and_render()
                return True
            elif keyval in (Gdk.KEY_plus, Gdk.KEY_equal):
                self.adjust_zoom(+0.1)
                return True
            elif keyval == Gdk.KEY_minus:
                self.adjust_zoom(-0.1)
                return True
            elif keyval == Gdk.KEY_0:
                self.reset_zoom()
                return True
            elif keyval in (Gdk.KEY_w, Gdk.KEY_W, Gdk.KEY_q, Gdk.KEY_Q):
                self.close()
                return True
        return False

    def toggle_mode(self):
        """Switches between Preview Mode and Editor Mode."""
        if self.current_mode == "preview":
            # Switch to Editor
            self.current_mode = "editor"
            self.mode_btn.set_icon_name("text-markdown-symbolic")
            self.mode_btn.set_tooltip_text("Switch to Preview Mode (Ctrl+E)")
            self.save_btn.set_visible(True)
            self.toc_button.set_sensitive(False)

            # Load raw content into editor buffer
            try:
                with open(self.file_path, "r", encoding="utf-8", errors="replace") as f:
                    raw_text = f.read()
                self.editor_buffer.set_text(raw_text)
                self.editor_buffer.set_modified(False)
                self.save_btn.set_sensitive(False)
            except Exception as e:
                self.editor_buffer.set_text(f"Error loading file: {e}")

            self.stack.set_visible_child_name("editor")
            self.source_view.grab_focus()
        else:
            # Switch to Preview (auto-save if modified)
            if self.editor_buffer.get_modified():
                self.save_file()

            self.current_mode = "preview"
            self.mode_btn.set_icon_name("document-edit-symbolic")
            self.mode_btn.set_tooltip_text("Switch to Editor Mode (Ctrl+E)")
            self.save_btn.set_visible(False)
            self.toc_button.set_sensitive(True)

            self.load_and_render()
            self.stack.set_visible_child_name("preview")

    def on_buffer_modified_changed(self, buffer):
        modified = buffer.get_modified()
        self.save_btn.set_sensitive(modified)
        if modified:
            self.win_title.set_subtitle(f"● {self.original_subtitle} (Modified)")
        else:
            self.win_title.set_subtitle(self.original_subtitle)

    def save_file(self):
        """Saves editor buffer contents to disk."""
        if not self.editor_buffer.get_modified() and self.current_mode != "editor":
            return

        start = self.editor_buffer.get_start_iter()
        end = self.editor_buffer.get_end_iter()
        text = self.editor_buffer.get_text(start, end, True)

        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.editor_buffer.set_modified(False)
            self.save_btn.set_sensitive(False)
            self.win_title.set_subtitle(self.original_subtitle)
        except Exception as e:
            dialog = Adw.MessageDialog(
                transient_for=self,
                heading="Error Saving File",
                body=str(e)
            )
            dialog.add_response("ok", "OK")
            dialog.present()

    def load_and_render(self):
        if not os.path.exists(self.file_path):
            self.webview.load_html(
                f"<div style='padding:40px;text-align:center;'><h2>File Not Found</h2><p>{self.file_path}</p></div>",
                "file:///"
            )
            return

        try:
            with open(self.file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            html_output, toc, stats = self.renderer.render(content, self.file_path)
            self.toc_items = toc
            self.stats = stats

            self.update_toc_ui()
            self.update_stats_ui()

            base_uri = "file://" + os.path.dirname(self.file_path) + "/"
            self.webview.load_html(html_output, base_uri)
            self.apply_theme_to_webview()
        except Exception as e:
            self.webview.load_html(
                f"<div style='padding:40px;color:red;'><h2>Error Rendering Markdown</h2><pre>{e}</pre></div>",
                "file:///"
            )

    def update_toc_ui(self):
        while True:
            row = self.toc_listbox.get_first_child()
            if not row:
                break
            self.toc_listbox.remove(row)

        if not self.toc_items:
            empty_lbl = Gtk.Label(label="No headings found", xalign=0)
            empty_lbl.add_css_class("dim-label")
            empty_lbl.set_margin_top(12)
            empty_lbl.set_margin_bottom(12)
            empty_lbl.set_margin_start(16)
            self.toc_listbox.append(empty_lbl)
            return

        for level, h_id, title in self.toc_items:
            btn = Gtk.Button(label=title)
            child = btn.get_child()
            if isinstance(child, Gtk.Label):
                child.set_xalign(0)
            btn.add_css_class("flat")
            btn.set_margin_start((level - 1) * 16 + 6)
            btn.set_margin_end(6)
            btn.connect("clicked", self.on_toc_item_clicked, h_id)
            self.toc_listbox.append(btn)

    def on_toc_item_clicked(self, _button, h_id: str):
        self.toc_popover.popdown()
        js = f"scrollToHeader('{h_id}');"
        self.webview.evaluate_javascript(js, -1, None, None, None, None)

    def update_stats_ui(self):
        self.lbl_stats_words.set_markup(f"<b>Words:</b> {self.stats.get('words', '0')}")
        self.lbl_stats_chars.set_markup(f"<b>Characters:</b> {self.stats.get('chars', '0')}")
        self.lbl_stats_time.set_markup(f"<b>Reading Time:</b> {self.stats.get('read_time', '~1 min')}")

    def adjust_zoom(self, delta: float):
        self.zoom_level = max(0.5, min(2.5, self.zoom_level + delta))
        self.webview.set_zoom_level(self.zoom_level)

    def reset_zoom(self):
        self.zoom_level = 1.0
        self.webview.set_zoom_level(1.0)

    def on_cycle_theme(self, _button):
        if self.theme_mode == "auto":
            self.theme_mode = "dark"
            self.theme_btn.set_icon_name("weather-clear-night-symbolic")
            self.theme_btn.set_tooltip_text("Theme: Dark (Click for Light)")
            self.update_editor_theme(True)
        elif self.theme_mode == "dark":
            self.theme_mode = "light"
            self.theme_btn.set_icon_name("weather-clear-symbolic")
            self.theme_btn.set_tooltip_text("Theme: Light (Click for Auto)")
            self.update_editor_theme(False)
        else:
            self.theme_mode = "auto"
            self.theme_btn.set_icon_name("emblem-system-symbolic")
            self.theme_btn.set_tooltip_text("Theme: Auto (Matches System)")
            is_dark = Adw.StyleManager.get_default().get_dark()
            self.update_editor_theme(is_dark)

        self.apply_theme_to_webview()

    def on_system_theme_changed(self, _style_manager, _pspec):
        if self.theme_mode == "auto":
            is_dark = Adw.StyleManager.get_default().get_dark()
            self.update_editor_theme(is_dark)
            self.apply_theme_to_webview()

    def apply_theme_to_webview(self):
        target = self.theme_mode
        if target == "auto":
            is_dark = Adw.StyleManager.get_default().get_dark()
            target = "dark" if is_dark else "light"

        js = f"if (typeof setTheme === 'function') setTheme('{target}');"
        self.webview.evaluate_javascript(js, -1, None, None, None, None)

    def on_search_toggle(self, button: Gtk.ToggleButton):
        active = button.get_active()
        self.search_bar.set_search_mode(active)
        if active:
            self.search_entry.grab_focus()
        else:
            self.find_controller.search_finish()
            self.lbl_search_count.set_text("")

    def on_search_text_changed(self, entry: Gtk.SearchEntry):
        text = entry.get_text()
        if not text:
            self.find_controller.search_finish()
            self.lbl_search_count.set_text("")
            return

        options = WebKit.FindOptions.CASE_INSENSITIVE | WebKit.FindOptions.WRAP_AROUND
        self.find_controller.search(text, options, 1000)
        self.find_controller.count_matches(text, options, 1000)

    def find_next(self):
        self.find_controller.search_next()

    def find_prev(self):
        self.find_controller.search_previous()

    def on_find_counted_matches(self, _controller, match_count: int):
        if match_count == 0:
            self.lbl_search_count.set_text("No matches")
        else:
            self.lbl_search_count.set_text(f"{match_count} matches")

    def on_find_found_text(self, _controller, _match_count: int):
        pass

    def on_find_failed(self, _controller):
        self.lbl_search_count.set_text("No matches")

    def on_decide_policy(self, _webview, decision, decision_type):
        if decision_type == WebKit.PolicyDecisionType.NAVIGATION_ACTION:
            action = decision.get_navigation_action()
            uri = action.get_request().get_uri()
            if uri.startswith(("http://", "https://", "mailto:")):
                decision.ignore()
                Gtk.show_uri(self, uri, Gdk.CURRENT_TIME)
                return True
        return False

    def setup_file_monitor(self):
        gfile = Gio.File.new_for_path(self.file_path)
        self.file_monitor = gfile.monitor_file(Gio.FileMonitorFlags.NONE, None)
        self.file_monitor.connect("changed", self.on_file_changed_on_disk)

    def on_file_changed_on_disk(self, _monitor, _file, _other_file, event_type):
        if event_type in (Gio.FileMonitorEvent.CHANGES_DONE_HINT, Gio.FileMonitorEvent.CHANGED):
            # Only hot-reload if we are in preview mode and not actively editing
            if self.current_mode == "preview":
                if self.reload_timeout_id != 0:
                    GLib.source_remove(self.reload_timeout_id)
                self.reload_timeout_id = GLib.timeout_add(250, self._debounced_reload)

    def _debounced_reload(self):
        self.reload_timeout_id = 0
        self.load_and_render()
        return False


class MarkdownViewerApp(Adw.Application):
    def __init__(self, target_file: str = ""):
        super().__init__(
            application_id="io.github.markdown_previewer",
            flags=Gio.ApplicationFlags.HANDLES_OPEN | Gio.ApplicationFlags.NON_UNIQUE
        )
        self.target_file = target_file

    def do_activate(self):
        win = MarkdownViewerWindow(self, self.target_file)
        win.present()

    def do_open(self, files, _n_files, _hint):
        if files:
            path = files[0].get_path()
            win = MarkdownViewerWindow(self, path)
            win.present()
        else:
            self.do_activate()


def main():
    if len(sys.argv) < 2:
        print("Usage: markdown-preview <file.md>")
        sys.exit(1)

    target_path = sys.argv[1]
    if target_path.startswith("file://"):
        from urllib.parse import unquote, urlparse
        target_path = unquote(urlparse(target_path).path)

    app = MarkdownViewerApp(target_path)
    app.run(None)


if __name__ == "__main__":
    main()
