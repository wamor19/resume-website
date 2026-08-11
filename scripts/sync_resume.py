"""
Sync everything from the Word CV.

The Word file is the primary copy. Run this after editing it in Word:

    python scripts/sync_resume.py          (or: npm run resume:sync)

Steps:
  1. Reformat the Word file for consistency and ATS readability, fitting 2 pages.
  2. Export the PDF the site links to.
  3. Update the CV-derived sections of index.html and bump the footer timestamp.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import export_pdf  # noqa: E402
import format_resume_docx  # noqa: E402
import sync_site_from_docx  # noqa: E402


def main() -> None:
    print("[1/3] Formatting the Word CV")
    format_resume_docx.main()

    print("\n[2/3] Exporting the PDF")
    archived = export_pdf.export()
    if archived is not None:
        kept = len(list(export_pdf.HISTORY_DIR.glob("*.pdf")))
        print(
            f"Kept previous version as {archived.relative_to(export_pdf.ROOT)} "
            f"({kept} in history)"
        )
    print(f"Wrote {export_pdf.PDF.relative_to(export_pdf.ROOT)}")

    print("\n[3/3] Updating the site")
    sync_site_from_docx.main()

    print("\nWord, PDF, and site are in sync.")


if __name__ == "__main__":
    main()
