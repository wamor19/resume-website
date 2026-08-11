"""Hyperlink helper for the Word CV contact line."""
from __future__ import annotations

from docx.oxml import OxmlElement
from docx.oxml.ns import qn

# Word's standard hyperlink blue, underlined, so links read as links on paper too.
LINK_COLOR = "0563C1"


def add_hyperlink(paragraph, text: str, url: str, *, size_pt: float) -> None:
    """Append a clickable run to `paragraph`. Callers own the display text."""
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
