"""Safe document writes shared by the standalone viewer and Nautilus panel."""

import os
import stat
import tempfile
from pathlib import Path


def save_document(file_path: str, text: str, original: str) -> None:
    """Replace a file atomically, refusing to overwrite an external edit."""
    path = Path(file_path).resolve(strict=True)
    if path.read_text(encoding="utf-8") != original:
        raise OSError(
            "This file changed outside the viewer. Your edits are still in the editor. "
            "Copy them before reopening the file to reconcile both versions."
        )

    permissions = stat.S_IMODE(path.stat().st_mode)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
            os.fchmod(stream.fileno(), permissions)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
