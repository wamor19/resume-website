"""
Retired: this used to build the Word CV from index.html.

The Word file is now the primary copy of the CV and the site is downstream, so
running the old direction would overwrite hand-edited Word content. Use:

    python scripts/sync_resume.py     (Word -> PDF + site)

Individual steps live in format_resume_docx.py, export_pdf.py and
sync_site_from_docx.py.
"""
from __future__ import annotations

import sys

MESSAGE = __doc__.strip()

if __name__ == "__main__":
    print(MESSAGE, file=sys.stderr)
    sys.exit(1)
