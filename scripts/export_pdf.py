"""Export the current Word CV to the site PDF (Word is source of truth)."""
from pathlib import Path

from docx2pdf import convert

ROOT = Path(__file__).resolve().parents[1]
DOCX = ROOT / "assets" / "files" / "william-amor-resume.docx"
PDF = ROOT / "assets" / "files" / "william-amor-cv-apr-2026.pdf"

if __name__ == "__main__":
    if not DOCX.exists():
        raise SystemExit(f"Missing {DOCX}")
    if PDF.exists():
        PDF.unlink()
    convert(str(DOCX), str(PDF))
    print(f"Wrote {PDF.relative_to(ROOT)}")
