"""
Convert the Word CV to the PDF the site links to.

Pure conversion: formatting is owned by scripts/format_resume_docx.py, so this
must not touch fonts, spacing or the contact line.

The PDF being replaced is copied into backups/pdf first. That history is kept
forever, so any earlier version can be retrieved. The site always links to the
one master copy in assets/files.

    python scripts/export_pdf.py
"""
from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from word_com import WD_FORMAT_PDF, WordUnavailable, opened, word_app  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "assets" / "files" / "Resume (William Amor).docx"
PDF = ROOT / "assets" / "files" / "Resume (William Amor).pdf"
HISTORY_DIR = ROOT / "backups" / "pdf"


def archive(pdf: Path = PDF) -> Path | None:
    """Copy `pdf` into the history folder, which is never pruned."""
    if not pdf.exists():
        return None

    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    # Stamped with when that PDF was built, not when it was archived, so a failed
    # export followed by a retry re-archives the same file rather than duplicating it.
    stamp = datetime.fromtimestamp(pdf.stat().st_mtime).strftime("%Y-%m-%d %H-%M-%S")
    dest = HISTORY_DIR / f"{pdf.stem} {stamp}.pdf"
    if not dest.exists():
        shutil.copy2(pdf, dest)
    return dest


def export(docx: Path = DOCX, pdf: Path = PDF) -> Path | None:
    pdf.parent.mkdir(parents=True, exist_ok=True)
    archived = archive(pdf)
    if pdf.exists():
        try:
            pdf.unlink()
        except PermissionError as exc:
            raise SystemExit(f"Cannot replace {pdf.name} - close any PDF viewer and retry.") from exc

    try:
        with word_app() as app, opened(app, docx) as doc:
            # SaveAs rather than ExportAsFixedFormat: it is what keeps the
            # contact line's hyperlinks clickable in the exported PDF.
            doc.SaveAs(str(pdf.resolve()), FileFormat=WD_FORMAT_PDF)
    except WordUnavailable as exc:
        raise SystemExit(f"Word is needed to write the PDF: {exc}") from exc

    if not pdf.exists():
        raise SystemExit(f"Word did not produce {pdf.name}.")
    return archived


if __name__ == "__main__":
    if not DOCX.exists():
        raise SystemExit(f"Missing {DOCX}")
    archived = export()
    if archived is not None:
        kept = len(list(HISTORY_DIR.glob("*.pdf")))
        print(f"Kept previous version as {archived.relative_to(ROOT)} ({kept} in history)")
    print(f"Wrote {PDF.relative_to(ROOT)}", file=sys.stdout)
