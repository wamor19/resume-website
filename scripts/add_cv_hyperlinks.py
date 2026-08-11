"""
Retired: this used to stamp a hardcoded contact line into the Word CV.

The Word file is now the primary copy of the CV, so the contact line is built
from whatever the Word file says. This script carried its own copy of the job
title, location and URLs, and running it would silently revert them. Use:

    python scripts/sync_resume.py     (Word -> PDF + site)

Contact-line formatting now lives in format_resume_docx.py; the hyperlink
element helper it uses is add_hyperlink in cv_hyperlinks.py.
"""
from __future__ import annotations

import sys

MESSAGE = __doc__.strip()

if __name__ == "__main__":
    print(MESSAGE, file=sys.stderr)
    sys.exit(1)
