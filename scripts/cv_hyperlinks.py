"""Hyperlink helpers for the Word CV contact line."""
from __future__ import annotations

import sys
from pathlib import Path

from docx.oxml import OxmlElement

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cv_fonts import FONT_CONTACT_PT  # noqa: E402

DEFAULT_EMAIL = "message@william-amor.info"
from docx.oxml.ns import qn
from docx.shared import Pt

LINK_COLOR = "0563C1"
LINKEDIN_URL = "https://www.linkedin.com/in/willamor/"


def _append_run(paragraph, text: str, *, size_pt: float = FONT_CONTACT_PT, link: bool = False) -> None:
    if not text:
        return
    if link:
        add_hyperlink(paragraph, text, _url_for_text(text))
        return
    run = paragraph.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(size_pt)


def _url_for_text(text: str) -> str:
    if "@" in text:
        return f"mailto:{text.strip()}"
    if "linkedin" in text.lower():
        return LINKEDIN_URL
    return text


def add_hyperlink(paragraph, text: str, url: str, *, size_pt: float = FONT_CONTACT_PT) -> None:
    part = paragraph.part
    r_id = part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True,
    )

    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)

    new_run = OxmlElement("w:r")
    r_pr = OxmlElement("w:rPr")

    color = OxmlElement("w:color")
    color.set(qn("w:val"), LINK_COLOR)
    r_pr.append(color)

    underline = OxmlElement("w:u")
    underline.set(qn("w:val"), "single")
    r_pr.append(underline)

    size = OxmlElement("w:sz")
    size.set(qn("w:val"), str(int(size_pt * 2)))
    r_pr.append(size)

    fonts = OxmlElement("w:rFonts")
    fonts.set(qn("w:ascii"), "Calibri")
    fonts.set(qn("w:hAnsi"), "Calibri")
    r_pr.append(fonts)

    new_run.append(r_pr)
    text_el = OxmlElement("w:t")
    text_el.text = text
    new_run.append(text_el)
    hyperlink.append(new_run)
    paragraph._p.append(hyperlink)


def clear_paragraph(paragraph) -> None:
    """Remove runs/hyperlinks but keep paragraph properties (e.g. center alignment)."""
    element = paragraph._element
    for child in list(element):
        tag = child.tag.split("}")[-1]
        if tag == "pPr":
            continue
        element.remove(child)


def ensure_paragraph_centered(paragraph) -> None:
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_pr = paragraph._element.find(qn("w:pPr"))
    if p_pr is None:
        p_pr = OxmlElement("w:pPr")
        paragraph._element.insert(0, p_pr)
    jc = p_pr.find(qn("w:jc"))
    if jc is None:
        jc = OxmlElement("w:jc")
        p_pr.append(jc)
    jc.set(qn("w:val"), "center")


def fill_contact_line(paragraph, email: str, *, size_pt: float = FONT_CONTACT_PT) -> None:
    clear_paragraph(paragraph)
    _append_run(paragraph, "Principal Product Owner  |  London, UK  |  ", size_pt=size_pt)
    add_hyperlink(paragraph, email, f"mailto:{email}", size_pt=size_pt)
    _append_run(paragraph, "  |  ", size_pt=size_pt)
    add_hyperlink(paragraph, "linkedin.com/in/willamor", LINKEDIN_URL, size_pt=size_pt)
    ensure_paragraph_centered(paragraph)
