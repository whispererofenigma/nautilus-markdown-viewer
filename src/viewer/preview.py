"""A persistent WebKit document for low-latency embedded previews."""

import json
import logging
import os
from pathlib import Path

from gi.repository import GLib, WebKit
from renderer import MarkdownRenderer


class PersistentPreview:
    """Warm WebKit once, then replace content without page navigation."""

    def __init__(self, webview, on_ready=None, on_error=None):
        self.webview = webview
        self.on_ready = on_ready
        self.on_error = on_error
        self._timeout_id = 0
        self._active_path = None
        self._recover_on_request = False
        self.last_metrics = {}
        policy = os.environ.get("MARKDOWN_PREVIEW_ACCELERATION", "never")
        if policy in ("always", "never"):
            webview.get_settings().set_hardware_acceleration_policy(
                WebKit.HardwareAccelerationPolicy.ALWAYS
                if policy == "always"
                else WebKit.HardwareAccelerationPolicy.NEVER
            )
        self._ready = False
        self._closed = False
        self._recovery_attempted = False
        self._pending = None
        self.revision = 0
        self.applied_revision = 0
        self._manager = webview.get_user_content_manager()
        self._manager.register_script_message_handler("markdownPreviewReady", None)
        self._message_handler = self._manager.connect(
            "script-message-received::markdownPreviewReady", self._on_frame_ready
        )
        self._termination_handler = webview.connect(
            "web-process-terminated", self._on_process_terminated
        )
        self._load_handler = webview.connect("load-changed", self._on_load_changed)
        shell, _, _ = MarkdownRenderer().render("", "")
        webview.load_html(shell, "file:///")

    def show(self, html, file_path):
        if self._closed:
            return
        self._recovery_attempted = False
        self._cancel_timeout()
        self._timeout_id = GLib.timeout_add_seconds(15, self._on_timeout)
        self.revision += 1
        self._active_path = file_path
        self._pending = (html, file_path, self.revision)
        if self._recover_on_request:
            self._recover_on_request = False
            self._ready = False
            shell, _, _ = MarkdownRenderer().render("", "")
            self.webview.load_html(shell, "file:///")
        if self._ready:
            self._apply_pending()

    def _on_load_changed(self, _webview, event):
        if event == WebKit.LoadEvent.STARTED:
            self._ready = False
        elif event == WebKit.LoadEvent.FINISHED:
            self._ready = True
            self._apply_pending()

    def _apply_pending(self):
        if self._pending is None:
            return
        html, file_path, revision = self._pending
        self._pending = None
        arguments = json.dumps(
            [
                html,
                Path(file_path).parent.as_uri() + "/",
                "md_scroll_" + file_path,
                Path(file_path).name,
                revision,
            ]
        )
        script = f"replaceDocument(...{arguments});"
        self.webview.evaluate_javascript(
            script, -1, None, None, None, self._on_applied, (html, file_path, revision)
        )

    def _on_applied(self, webview, result, request):
        html, file_path, revision = request
        if self._closed:
            return
        try:
            self.last_metrics = json.loads(
                webview.evaluate_javascript_finish(result).to_string()
            )
        except Exception as error:
            if revision != self.revision:
                return
            if self._recovery_attempted:
                logging.warning("Preview update failed: %s", error)
                self._fail(str(error))
                return
            self._recovery_attempted = True
            self._pending = request
            self._ready = False
            shell, _, _ = MarkdownRenderer().render("", "")
            webview.load_html(shell, "file:///")
            return
        self.applied_revision = revision

    def _on_frame_ready(self, _manager, value):
        try:
            revision = int(value.to_string())
        except (ValueError, AttributeError):
            return
        if not self._closed and revision == self.revision:
            self._cancel_timeout()
            if self.on_ready:
                self.on_ready(self._active_path, revision)

    def _on_process_terminated(self, _webview, _reason):
        self._ready = False
        self._fail("The browser process stopped. Use Reload to restart the preview.")

    def _cancel_timeout(self):
        if self._timeout_id:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = 0

    def _on_timeout(self):
        self._timeout_id = 0
        self._fail("The preview is taking too long. Use Reload to try again.")
        return False

    def _fail(self, message):
        self._recover_on_request = True
        self._cancel_timeout()
        if not self._closed and self.on_error:
            self.on_error(message)

    def close(self):
        self._closed = True
        self._cancel_timeout()
        self._pending = None
        self.webview.disconnect(self._load_handler)
        self.webview.disconnect(self._termination_handler)
        self._manager.disconnect(self._message_handler)
        self._manager.unregister_script_message_handler("markdownPreviewReady", None)
