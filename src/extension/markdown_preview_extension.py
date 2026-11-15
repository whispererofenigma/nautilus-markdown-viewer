"""Nautilus 4.0 Python Extension: Markdown Previewer & Embedded Side Panel.
Provides:
1. Standalone Window viewer via right-click ("Preview Markdown").
2. Embedded, horizontally draggable and stretchable side panel inside the Nautilus window.
3. Header bar toggle button right in the file explorer to open/close the preview panel.
4. Auto-display of any Markdown file selected in the explorer pane (Icon or List view).
"""

import os
import sys
import subprocess
from urllib.parse import unquote, urlparse

# Set WebKitGTK sandbox environment variable for Ubuntu 24.04
os.environ["WEBKIT_DISABLE_SANDBOX_THIS_IS_DANGEROUS"] = "1"

# Add viewer package to sys.path
VIEWER_DIR = os.path.expanduser("~/.local/share/nautilus-markdown-viewer")
if not os.path.isdir(VIEWER_DIR):
    VIEWER_DIR = "/usr/share/nautilus-markdown-viewer"
if VIEWER_DIR not in sys.path:
    sys.path.insert(0, VIEWER_DIR)

import gi

gi.require_version("Nautilus", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("WebKit", "6.0")
from gi.repository import GObject, Nautilus, Gtk, Gdk, Adw, GLib

from panel import MarkdownSidePanel

MARKDOWN_EXTENSIONS = {".md", ".markdown", ".mdown", ".mkd", ".mdwn", ".mdx", ".rmd"}

MARKDOWN_MIMETYPES = {"text/markdown", "text/x-markdown", "text/x-web-markdown"}

PREVIEWER_BIN = os.path.expanduser("~/.local/bin/markdown-preview")
if not os.path.exists(PREVIEWER_BIN):
    PREVIEWER_BIN = os.path.join(VIEWER_DIR, "markdown-preview")


def find_widgets_by_class(root, cls):
    """Recursively search GTK widget tree for instances of a given class."""
    results = []
    if isinstance(root, cls):
        results.append(root)
    child = root.get_first_child()
    while child:
        results.extend(find_widgets_by_class(child, cls))
        child = child.get_next_sibling()
    return results


def find_file_views(root):
    """Find view containers without walking thousands of file-item widgets."""
    if isinstance(root, (Gtk.GridView, Gtk.ColumnView)):
        return [root]
    if isinstance(root, MarkdownSidePanel):
        return []
    views = []
    child = root.get_first_child()
    while child:
        views.extend(find_file_views(child))
        child = child.get_next_sibling()
    return views


class MarkdownPreviewExtension(GObject.GObject, Nautilus.MenuProvider):
    def __init__(self):
        super().__init__()
        self.windows_installed = set()
        self.window_data = {}  # window_id -> {paned, panel, toggle_btn, hooked_views}

        # Register local icons directory
        try:
            display = Gdk.Display.get_default()
            if display:
                theme = Gtk.IconTheme.get_for_display(display)
                icon_dir = os.path.expanduser(
                    "~/.local/share/icons/hicolor/scalable/actions"
                )
                if icon_dir not in theme.get_search_path():
                    theme.add_search_path(icon_dir)
        except Exception:
            pass

        # Connect to Nautilus application
        app = Gtk.Application.get_default()
        if app:
            app.connect("window-added", self.on_window_added)
            for win in app.get_windows():
                self.setup_window(win)

    # ==============================================================
    # Nautilus Menu Provider (Context Menus)
    # ==============================================================
    def _is_markdown(self, file_info: Nautilus.FileInfo) -> bool:
        if file_info.is_directory() or file_info.get_uri_scheme() != "file":
            return False

        name = file_info.get_name().lower()
        _, ext = os.path.splitext(name)
        if ext in MARKDOWN_EXTENSIONS:
            return True

        mime = file_info.get_mime_type()
        if mime in MARKDOWN_MIMETYPES:
            return True

        return False

    def get_file_items(self, files: list[Nautilus.FileInfo]) -> list[Nautilus.MenuItem]:
        md_paths = []
        for f in files:
            if self._is_markdown(f):
                path = unquote(urlparse(f.get_uri()).path)
                md_paths.append(path)

        if not md_paths:
            return []

        item = Nautilus.MenuItem(
            name="MarkdownPreview::Preview",
            label="Preview Markdown (New Window)",
            tip="Open rich Markdown preview in standalone window",
            icon="text-markdown-symbolic",
        )
        item.connect("activate", self._on_activate_standalone, md_paths)
        return [item]

    def get_background_items(
        self, current_folder: Nautilus.FileInfo
    ) -> list[Nautilus.MenuItem]:
        item = Nautilus.MenuItem(
            name="MarkdownPreview::TogglePanel",
            label="Toggle Markdown Preview Panel",
            tip="Show or hide the embedded Markdown preview side panel",
            icon="text-markdown-symbolic",
        )
        item.connect("activate", self._on_toggle_panel_from_menu)
        return [item]

    def _on_activate_standalone(self, _menu_item, paths: list[str]):
        for path in paths:
            subprocess.Popen([PREVIEWER_BIN, path], start_new_session=True)

    def _on_toggle_panel_from_menu(self, _menu_item):
        app = Gtk.Application.get_default()
        if app:
            active_win = app.get_active_window()
            if active_win and id(active_win) in self.window_data:
                btn = self.window_data[id(active_win)].get("toggle_btn")
                if btn:
                    btn.set_active(not btn.get_active())

    # ==============================================================
    # Embedded Side Panel & Explorer Integration
    # ==============================================================
    def on_window_added(self, _app, window):
        GLib.timeout_add(500, self.setup_window, window)

    def setup_window(self, window):
        win_id = id(window)
        if win_id in self.windows_installed:
            return False

        # Locate the main ToolbarView (the one containing TabView)
        if not hasattr(Adw, "ToolbarView"):
            return False
        tb_views = find_widgets_by_class(window, Adw.ToolbarView)
        main_tb = None
        for tb in tb_views:
            content = tb.get_content()
            if content and isinstance(content, Adw.TabView):
                main_tb = tb
                break

        if not main_tb:
            return False

        tab_view = main_tb.get_content()
        headerbars = find_widgets_by_class(main_tb, Adw.HeaderBar)
        if not headerbars:
            return False

        main_header = headerbars[0]

        # 1. Create the Draggable and Stretchable Splitter (Gtk.Paned)
        paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        paned.set_wide_handle(True)
        paned.set_resize_start_child(True)
        paned.set_resize_end_child(True)
        paned.set_shrink_start_child(False)
        paned.set_shrink_end_child(False)

        # 2. Create the Markdown Side Panel
        side_panel = MarkdownSidePanel(
            on_close_callback=lambda: toggle_btn.set_active(False)
        )
        side_panel.set_visible(False)

        # 3. Embed TabView into Paned, and Paned into ToolbarView
        main_tb.set_content(None)
        paned.set_start_child(tab_view)
        paned.set_end_child(side_panel)
        main_tb.set_content(paned)

        def init_splitter_position():
            alloc = paned.get_allocation()
            if alloc.width > 600:
                paned.set_position(max(300, alloc.width - 440))
            else:
                paned.set_position(450)
            return False

        # 4. Add the Toggle Button right into the Nautilus HeaderBar
        toggle_btn = Gtk.ToggleButton(
            icon_name="text-markdown-symbolic",
            tooltip_text="Toggle Markdown Preview Panel",
        )
        toggle_btn.add_css_class("flat")

        def on_toggle_clicked(btn):
            active = btn.get_active()
            if not active and side_panel.editor_buffer.get_modified():
                if not side_panel.save_file():
                    btn.set_active(True)
                    return
            side_panel.set_visible(active)
            if active:
                init_splitter_position()
                self.hook_views_in_window(window)
                self.update_panel_selection(window, side_panel, force=True)

        toggle_btn.connect("toggled", on_toggle_clicked)
        main_header.pack_end(toggle_btn)

        # 5. Store window references
        self.window_data[win_id] = {
            "paned": paned,
            "panel": side_panel,
            "toggle_btn": toggle_btn,
            "hooked_views": {},
            "view_handlers": {},
            "tab_view": tab_view,
            "last_selection": object(),
        }
        self.windows_installed.add(win_id)

        # 6. Hook selection signals on file explorer views
        self.hook_views_in_window(window)

        # Periodically check for new views / folder navigations
        self.window_data[win_id]["refresh_source"] = GLib.timeout_add(
            100, self.refresh_views_periodically, window
        )
        window.connect("close-request", self.on_window_close)
        window.connect("destroy", lambda _window: self.cleanup_window(window))
        return False

    def hook_views_in_window(self, window):
        win_id = id(window)
        if win_id not in self.window_data:
            return

        data = self.window_data[win_id]
        panel = data["panel"]
        hooked = data["hooked_views"]

        # Bind public GTK selection models rather than private Nautilus signals.
        # Models can change while the view widget itself remains alive.
        for model_id, (view, model, handler) in list(hooked.items()):
            if view.get_root() is not window or view.get_model() is not model:
                model.disconnect(handler)
                del hooked[model_id]

        page = data["tab_view"].get_selected_page()
        views = find_file_views(page.get_child()) if page else []
        handlers = data["view_handlers"]
        for view_id, (view, handler) in list(handlers.items()):
            if view.get_root() is not window:
                view.disconnect(handler)
                del handlers[view_id]
        for view in views:
            if id(view) not in handlers:
                handler = view.connect(
                    "notify::model",
                    lambda *_args: self.refresh_views_periodically(window),
                )
                handlers[id(view)] = (view, handler)
            model = view.get_model()
            if model is None or id(model) in hooked:
                continue
            handler = model.connect(
                "selection-changed",
                lambda *_args: self.update_panel_selection(window, panel),
            )
            hooked[id(model)] = (view, model, handler)

    def refresh_views_periodically(self, window):
        if id(window) in self.windows_installed:
            if self.window_data[id(window)]["panel"].get_visible():
                self.hook_views_in_window(window)
                self.update_panel_selection(
                    window, self.window_data[id(window)]["panel"]
                )
            return True
        return False

    def on_window_close(self, window):
        data = self.window_data.get(id(window))
        if data and data["panel"].editor_buffer.get_modified():
            if not data["panel"].save_file():
                return True
        return False

    def cleanup_window(self, window):
        data = self.window_data.pop(id(window), None)
        self.windows_installed.discard(id(window))
        if data:
            GLib.source_remove(data["refresh_source"])
            for _view, model, handler in data["hooked_views"].values():
                model.disconnect(handler)
            for view, handler in data["view_handlers"].values():
                view.disconnect(handler)
            data["panel"].close_resources()

    def update_panel_selection(self, window, panel, force=False):
        if not panel.get_visible():
            return

        file_path = self.extract_selected_path(window)
        data = self.window_data.get(id(window))
        if data is None:
            return
        if not force and file_path == data["last_selection"]:
            return
        # Remember the event even if saving fails: polling must not reopen an
        # error dialog every 100 ms or undo a link opened inside the preview.
        data["last_selection"] = file_path
        panel.set_file(file_path)

    def extract_selected_path(self, window) -> str | None:
        """Read cached selection models; never traverse the file widget tree."""
        data = self.window_data.get(id(window))
        if data:
            for view, _model, _handler in data["hooked_views"].values():
                if view.get_mapped():
                    return self._extract_path_from_list_view(view)
        return None

    def _extract_path_from_list_view(self, view_widget) -> str | None:
        if not view_widget.get_mapped():
            return None
        model = view_widget.get_model()
        if not model or not hasattr(model, "get_selection"):
            return None

        bitset = model.get_selection()
        if not bitset or bitset.get_size() != 1:
            return None

        idx = bitset.get_nth(0)
        row = model.get_item(idx)
        if not row:
            return None

        # Row is typically a Gtk.TreeListRow
        item = row.get_item() if hasattr(row, "get_item") else row
        if not item:
            return None

        # Item is a NautilusViewItem, containing 'file' property (NautilusVFSFile)
        if hasattr(item, "get_property"):
            try:
                nautilus_file = item.get_property("file")
                if nautilus_file:
                    if hasattr(nautilus_file, "get_location"):
                        loc = nautilus_file.get_location()
                        if loc and hasattr(loc, "get_path"):
                            return loc.get_path()
                    if hasattr(nautilus_file, "get_uri"):
                        uri = nautilus_file.get_uri()
                        if uri:
                            return unquote(urlparse(uri).path)
            except Exception:
                pass

        return None
