"""
Word automation shared by the page counter and the PDF export.

Both steps drive Word in the same run, and plain `Dispatch` attaches to whatever
Word instance is already running. A previous step that is still shutting down,
or a stray instance sat behind a modal dialog, therefore gets reused and every
call on it fails with an unresolvable-attribute error. `DispatchEx` asks for a
private instance instead, which keeps the two steps independent.
"""
from __future__ import annotations

import gc
from contextlib import contextmanager
from pathlib import Path

WD_FORMAT_PDF = 17
WD_DO_NOT_SAVE_CHANGES = 0
WD_STATISTIC_PAGES = 2


class WordUnavailable(RuntimeError):
    """Word could not be driven: not installed, or refusing automation."""


@contextmanager
def word_app():
    """A private, invisible Word instance that is always shut down afterwards."""
    try:
        import pythoncom
        import win32com.client
    except ImportError as exc:
        raise WordUnavailable("pywin32 is not installed") from exc

    pythoncom.CoInitialize()
    app = None
    try:
        try:
            app = win32com.client.DispatchEx("Word.Application")
            app.Visible = False
            app.DisplayAlerts = False
        except Exception as exc:  # noqa: BLE001 - Word missing or blocked
            raise WordUnavailable(str(exc)) from exc
        yield app
    finally:
        if app is not None:
            try:
                app.Quit(WD_DO_NOT_SAVE_CHANGES)
            except Exception:  # noqa: BLE001 - already gone
                pass
        # Quit only asks Word to exit; it stays resident while Python still holds
        # a reference to it, so drop ours and collect before releasing COM.
        app = None
        gc.collect()
        pythoncom.CoUninitialize()


@contextmanager
def opened(app, path: Path):
    """Open a document read-only and always close it without saving."""
    doc = app.Documents.Open(
        str(Path(path).resolve()),
        ReadOnly=True,
        AddToRecentFiles=False,
        Visible=False,
    )
    try:
        yield doc
    finally:
        try:
            doc.Close(WD_DO_NOT_SAVE_CHANGES)
        except Exception:  # noqa: BLE001 - already closed
            pass
        doc = None
        gc.collect()
