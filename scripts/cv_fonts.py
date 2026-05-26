"""CV typography constants and helpers (Word/PDF)."""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt

# Calibri — modest bump (+0.5pt body, +1pt name) for readability on 2 pages.
FONT_NAME_PT = 19
FONT_CONTACT_PT = 10
FONT_SECTION_PT = 10.5
FONT_ROLE_TITLE_PT = 10.5
FONT_ROLE_META_PT = 9.5
FONT_BODY_PT = 9.5

_SECTION_HEADING_RE = re.compile(
    r"^(PROFESSIONAL SUMMARY|IMPACT HIGHLIGHTS|EXPERIENCE|EDUCATION|CERTIFICATIONS|SKILLS)"
)


def _set_hyperlink_sizes(paragraph, size_pt: float) -> None:
    half_points = str(int(size_pt * 2))
    for hyperlink in paragraph._element.findall(qn("w:hyperlink")):
        for sz in hyperlink.findall(".//" + qn("w:sz")):
            sz.set(qn("w:val"), half_points)


def _is_section_heading(paragraph) -> bool:
    text = paragraph.text.strip().upper()
    return bool(_SECTION_HEADING_RE.match(text))


def _apply_role_line(paragraph) -> None:
    """Role header: bold title + meta line."""
    for i, run in enumerate(paragraph.runs):
        pt = FONT_ROLE_TITLE_PT if (i == 0 and run.bold) else FONT_ROLE_META_PT
        run.font.size = Pt(pt)
        run.font.name = run.font.name or "Calibri"


def apply_fonts_to_document(doc: Document) -> None:
    for idx, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text.strip()
        if not text:
            continue

        if idx == 0:
            for run in paragraph.runs:
                run.font.size = Pt(FONT_NAME_PT)
                run.font.name = run.font.name or "Calibri"
            continue

        if idx == 1 or "@" in text or "linkedin.com" in text.lower():
            for run in paragraph.runs:
                run.font.size = Pt(FONT_CONTACT_PT)
                run.font.name = run.font.name or "Calibri"
            _set_hyperlink_sizes(paragraph, FONT_CONTACT_PT)
            continue

        if _is_section_heading(paragraph):
            for run in paragraph.runs:
                run.font.size = Pt(FONT_SECTION_PT)
                run.font.name = run.font.name or "Calibri"
            continue

        if paragraph.runs and paragraph.runs[0].bold and "  |  " in text:
            _apply_role_line(paragraph)
            continue

        if (
            paragraph.runs
            and paragraph.runs[0].bold
            and (" — " in text or " - " in text)
            and "  |  " not in text
        ):
            for i, run in enumerate(paragraph.runs):
                run.font.size = Pt(FONT_ROLE_TITLE_PT if i == 0 else FONT_ROLE_META_PT)
                run.font.name = run.font.name or "Calibri"
            continue

        for run in paragraph.runs:
            run.font.size = Pt(FONT_BODY_PT)
            run.font.name = run.font.name or "Calibri"


def apply_fonts_to_docx(path: Path) -> None:
    doc = Document(str(path))
    apply_fonts_to_document(doc)
    doc.save(str(path))


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    docx = root / "assets" / "files" / "Resume (William Amor).docx"
    if not docx.exists():
        raise SystemExit(f"Missing {docx}")
    apply_fonts_to_docx(docx)
    print(f"Updated fonts in {docx.relative_to(root)}")
