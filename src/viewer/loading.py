"""Coalesced background reads/renders; only the newest request reaches GTK."""

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path

from gi.repository import GLib
from renderer import MarkdownRenderer


class PreviewLoader:
    def __init__(self, renderer=None):
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="markdown"
        )
        self._renderer = renderer if renderer is not None else MarkdownRenderer()
        self._future = None
        self._generation = 0
        self._closed = False
        self._cache = OrderedDict()
        self._cache_bytes = 0

    def request(self, path, callback):
        if self._closed:
            return
        self.invalidate()
        generation = self._generation
        future = self._executor.submit(self._render, path)
        self._future = future

        def completed(result):
            if result.cancelled():
                return
            try:
                value, error = result.result(), None
            except Exception as exc:
                value, error = None, str(exc)
            GLib.idle_add(
                self._deliver,
                generation,
                callback,
                value,
                error,
                priority=GLib.PRIORITY_DEFAULT,
            )

        future.add_done_callback(completed)

    def _render(self, path):
        content = Path(path).read_text(encoding="utf-8", errors="replace")
        key = (path, sha256(content.encode("utf-8")).digest())
        cached = self._cache.get(key)
        if cached is not None:
            self._cache.move_to_end(key)
            return cached[0]

        result = self._renderer.render(content, path)
        size = len(result[0].encode("utf-8"))
        # Retain a small working set without growing with every visited file.
        if size <= 8 * 1024 * 1024:
            self._cache[key] = (result, size)
            self._cache_bytes += size
            while len(self._cache) > 8 or self._cache_bytes > 8 * 1024 * 1024:
                _, (_, removed_size) = self._cache.popitem(last=False)
                self._cache_bytes -= removed_size
        return result

    def _deliver(self, generation, callback, value, error):
        if not self._closed and generation == self._generation:
            callback(value, error)
        return False

    def invalidate(self):
        self._generation += 1
        if self._future:
            self._future.cancel()

    def close(self):
        self._closed = True
        self.invalidate()
        self._executor.shutdown(wait=False, cancel_futures=True)
