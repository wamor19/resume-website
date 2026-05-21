"""
Build Word + PDF CV from index.html (single source of truth: the site).

Run after editing resume copy on the site:
  python scripts/generate_resume_docx.py

Outputs:
  assets/files/william-amor-resume.docx
  assets/files/william-amor-cv-apr-2026.pdf  (site download link)
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

# Export trims longest roles so Word/PDF fit two pages; the site keeps full bullets.
DEFAULT_BULLET_CAPS: dict[str, int] = {
    "Principal Product Owner": 7,
    "Data & Analytics Product Owner (EMEA)": 6,
    "IT Business Technology Leader (Leadership Programme)": 5,
    "Intelligent Automation Product Manager (Leadership Programme)": 7,
    "Global Project Coordinator": 4,
    "Technology Business Partner (Placement) to Product Delivery Lead (Part-time)": 3,
}
EXPORT_BULLET_CAPS: dict[str, int] = {}
PAGE2_ROLE_INDEX = 3  # J&J Automation — everything from here starts page 2

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "index.html"
DOCX_PATH = ROOT / "assets" / "files" / "william-amor-resume.docx"
PDF_PATH = ROOT / "assets" / "files" / "william-amor-cv-apr-2026.pdf"


def strip_html(text: str) -> str:
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    text = text.replace("\u2011", "-").replace("\u00a0", " ")
    return re.sub(r"\s+", " ", text).strip()


def first_match(pattern: str, source: str, flags=0) -> str:
    m = re.search(pattern, source, flags)
    return strip_html(m.group(1)) if m else ""


def first_match_html(pattern: str, source: str, flags=0) -> str:
    m = re.search(pattern, source, flags)
    return m.group(1) if m else ""


def all_matches(pattern: str, source: str, flags=0) -> list[str]:
    return [strip_html(m.group(1)) for m in re.finditer(pattern, source, flags)]


def parse_resume_html(source: str) -> dict:
    email = first_match(r'data-email="([^"]+)"', source)

    ledes = all_matches(r'<p class="hero__lede">\s*(.*?)\s*</p>', source, re.DOTALL)
    summary = " ".join(ledes) if ledes else ""

    impact_block = first_match_html(
        r'<ul class="impactWins"[^>]*>(.*?)</ul>', source, re.DOTALL
    )
    impact = all_matches(r"<li>(.*?)</li>", impact_block, re.DOTALL) if impact_block else []

    roles = []
    for card in re.finditer(
        r'<article class="xpCard"[^>]*data-tags="([^"]*)"[^>]*>(.*?)</article>',
        source,
        re.DOTALL,
    ):
        block = card.group(2)
        title = first_match(r'<h3 class="xpCard__title">(.*?)</h3>', block, re.DOTALL)
        company = first_match(
            r'<span class="xpCard__orgName">(.*?)</span>', block, re.DOTALL
        )
        location = first_match(
            r'<span class="xpCard__orgLoc">(.*?)</span>', block, re.DOTALL
        )
        dates = first_match(r'<div class="xpCard__date">(.*?)</div>', block, re.DOTALL)
        dates = dates.replace(" to present", " – Present").replace(" to ", " – ")
        bullets_html = first_match_html(
            r'<ul class="bullets">\s*(.*?)\s*</ul>', block, re.DOTALL
        )
        bullet_items = (
            all_matches(r"<li>(.*?)</li>", bullets_html, re.DOTALL) if bullets_html else []
        )
        roles.append(
            {
                "title": title,
                "company": company,
                "location": location,
                "dates": dates,
                "bullets": bullet_items,
            }
        )

    edu_block = first_match(
        r'<section class="section" id="education"[^>]*>.*?<div class="eduChip">(.*?)</div>\s*</div>\s*</section>',
        source,
        re.DOTALL,
    )
    education = {
        "school": first_match(r'<div class="eduChip__h">(.*?)</div>', edu_block, re.DOTALL),
        "degree": first_match(
            r'<div class="eduChip__degree">(.*?)</div>', edu_block, re.DOTALL
        ),
        "grade": first_match(r'<div class="eduChip__grade">(.*?)</div>', edu_block, re.DOTALL),
        "bullets": [],
    }
    edu_bullets_html = first_match_html(
        r'<ul class="eduChip__bullets"[^>]*>(.*?)</ul>', edu_block, re.DOTALL
    )
    education["bullets"] = (
        all_matches(r"<li>(.*?)</li>", edu_bullets_html, re.DOTALL) if edu_bullets_html else []
    )

    cert_block = first_match_html(
        r'<section class="section" id="certificates"[^>]*>.*?<ul class="bullets"[^>]*>(.*?)</ul>',
        source,
        re.DOTALL,
    )
    certificates = (
        all_matches(r"<li>(.*?)</li>", cert_block, re.DOTALL) if cert_block else []
    )

    product_craft = first_match(
        r'id="toolbox-product">.*?<p class="skillFlow__p">\s*(.*?)\s*</p>',
        source,
        re.DOTALL,
    )
    data_stack = first_match(
        r'id="toolbox-stack">.*?<p class="skillFlow__p">\s*(.*?)\s*</p>',
        source,
        re.DOTALL,
    )
    chips = all_matches(r'<span class="chip">(.*?)</span>', source, re.DOTALL)

    return {
        "email": email,
        "summary": summary,
        "impact": impact,
        "roles": roles,
        "education": education,
        "certificates": certificates,
        "product_craft": product_craft,
        "data_stack": data_stack,
        "chips": chips,
    }


def set_doc_defaults(doc: Document) -> None:
    for section in doc.sections:
        section.top_margin = Inches(0.45)
        section.bottom_margin = Inches(0.45)
        section.left_margin = Inches(0.55)
        section.right_margin = Inches(0.55)


def style_paragraph(
    paragraph,
    size_pt: float,
    *,
    space_before: float = 0,
    space_after: float = 3,
    line_spacing: float = 1.12,
) -> None:
    fmt = paragraph.paragraph_format
    fmt.line_spacing_rule = WD_LINE_SPACING.MULTIPLE
    fmt.line_spacing = line_spacing
    fmt.space_before = Pt(space_before)
    fmt.space_after = Pt(space_after)
    for run in paragraph.runs:
        run.font.name = "Calibri"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
        run.font.size = Pt(size_pt)


def bullets_for_export(title: str, bullets: list[str]) -> list[str]:
    cap = EXPORT_BULLET_CAPS.get(title)
    if cap is None or len(bullets) <= cap:
        return bullets
    return bullets[:cap]


def add_section_heading(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text.upper())
    run.font.name = "Calibri"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
    run.font.size = Pt(10)
    run.font.bold = True
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True


def keep_block_together(paragraphs: list) -> None:
    """Keep a block (role, education, etc.) on one page when Word can fit it."""
    for i, para in enumerate(paragraphs):
        para.paragraph_format.keep_together = True
        para.paragraph_format.widow_control = True
        if i < len(paragraphs) - 1:
            para.paragraph_format.keep_with_next = True


def add_role(doc: Document, role: dict, *, page_break_before: bool = False) -> None:
    block: list = []

    p = doc.add_paragraph()
    if page_break_before:
        p.paragraph_format.page_break_before = True
    title_run = p.add_run(role["title"])
    title_run.bold = True
    title_run.font.size = Pt(10)
    title_run.font.name = "Calibri"
    meta = p.add_run(
        f"  |  {role['company']}  |  {role['location']}  |  {role['dates']}"
    )
    meta.font.size = Pt(9)
    meta.font.name = "Calibri"
    style_paragraph(p, 10, space_before=7, space_after=2)
    block.append(p)

    export_bullets = bullets_for_export(role["title"], role["bullets"])
    for j, bullet in enumerate(export_bullets):
        bp = doc.add_paragraph(bullet, style="List Bullet")
        bp.paragraph_format.left_indent = Inches(0.2)
        bp.paragraph_format.first_line_indent = Inches(-0.12)
        style_paragraph(
            bp,
            9,
            space_after=3 if j < len(export_bullets) - 1 else 5,
        )
        block.append(bp)

    keep_block_together(block)


def build_docx(data: dict) -> Document:
    doc = Document()
    set_doc_defaults(doc)

    h = doc.add_paragraph()
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name = h.add_run("William Amor")
    name.bold = True
    name.font.size = Pt(18)
    name.font.name = "Calibri"
    style_paragraph(h, 18, space_after=2)

    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact = sub.add_run(
        f"Principal Product Owner  |  London, UK  |  "
        f"{data['email']}  |  linkedin.com/in/willamor"
    )
    contact.font.size = Pt(9.5)
    contact.font.name = "Calibri"
    style_paragraph(sub, 9.5, space_after=10)

    add_section_heading(doc, "Professional Summary")
    sp = doc.add_paragraph(data["summary"])
    style_paragraph(sp, 9.5, space_after=4, line_spacing=1.15)

    if data["impact"]:
        add_section_heading(doc, "Selected Impact")
        for i, item in enumerate(data["impact"]):
            bp = doc.add_paragraph(item, style="List Bullet")
            bp.paragraph_format.left_indent = Inches(0.2)
            bp.paragraph_format.first_line_indent = Inches(-0.12)
            style_paragraph(
                bp,
                9,
                space_after=3 if i < len(data["impact"]) - 1 else 5,
            )

    add_section_heading(doc, "Experience")
    for i, role in enumerate(data["roles"]):
        add_role(doc, role, page_break_before=(i == PAGE2_ROLE_INDEX))

    edu = data["education"]
    if edu.get("school"):
        add_section_heading(doc, "Education")
        edu_block: list = []
        p = doc.add_paragraph()
        school = p.add_run(f"{edu['school']} — ")
        school.bold = True
        school.font.size = Pt(10)
        school.font.name = "Calibri"
        line = p.add_run(f"{edu.get('degree', '')}  |  {edu.get('grade', '')}")
        line.font.size = Pt(9)
        line.font.name = "Calibri"
        edu_block.append(p)
        style_paragraph(p, 9.5, space_after=3)
        edu_bullets = edu.get("bullets", [])
        for j, bullet in enumerate(edu_bullets):
            bp = doc.add_paragraph(bullet, style="List Bullet")
            bp.paragraph_format.left_indent = Inches(0.2)
            bp.paragraph_format.first_line_indent = Inches(-0.12)
            style_paragraph(
                bp,
                9,
                space_after=3 if j < len(edu_bullets) - 1 else 4,
            )
            edu_block.append(bp)
        keep_block_together(edu_block)

    if data["certificates"]:
        add_section_heading(doc, "Certifications")
        cp = doc.add_paragraph("; ".join(data["certificates"]))
        style_paragraph(cp, 9, space_after=4)

    add_section_heading(doc, "Skills & Platforms")
    if data["product_craft"]:
        p = doc.add_paragraph(data["product_craft"])
        style_paragraph(p, 9, space_after=4, line_spacing=1.15)
    if data["data_stack"]:
        p = doc.add_paragraph(data["data_stack"])
        style_paragraph(p, 9, space_after=2, line_spacing=1.15)

    return doc


def count_docx_pages(docx_path: Path) -> int | None:
    """Return page count using Word (Windows). None if Word automation unavailable."""
    try:
        import win32com.client
    except ImportError:
        return None

    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc = None
    try:
        doc = word.Documents.Open(str(docx_path.resolve()))
        return int(doc.ComputeStatistics(2))
    finally:
        if doc is not None:
            doc.Close(False)
        word.Quit()


def reset_export_caps() -> None:
    EXPORT_BULLET_CAPS.clear()
    EXPORT_BULLET_CAPS.update(DEFAULT_BULLET_CAPS)


def tighten_export_caps() -> None:
    for key in list(EXPORT_BULLET_CAPS.keys()):
        EXPORT_BULLET_CAPS[key] = max(3, EXPORT_BULLET_CAPS[key] - 1)


def export_pdf(docx_path: Path, pdf_path: Path) -> None:
    try:
        from docx2pdf import convert
    except ImportError as exc:
        raise SystemExit("docx2pdf is required: pip install docx2pdf") from exc

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        pdf_path.unlink()
    convert(str(docx_path), str(pdf_path))


def main() -> None:
    if not HTML_PATH.exists():
        print(f"Missing {HTML_PATH}", file=sys.stderr)
        sys.exit(1)

    source = HTML_PATH.read_text(encoding="utf-8")
    data = parse_resume_html(source)
    if not data["roles"]:
        print("No experience roles parsed from index.html", file=sys.stderr)
        sys.exit(1)

    DOCX_PATH.parent.mkdir(parents=True, exist_ok=True)
    reset_export_caps()

    for attempt in range(5):
        doc = build_docx(data)
        doc.save(DOCX_PATH)
        pages = count_docx_pages(DOCX_PATH)
        if pages is not None:
            print(f"Word pages: {pages}")
            if pages <= 2:
                break
            tighten_export_caps()
            print("Over 2 pages — tightening export bullet caps and rebuilding...", file=sys.stderr)
        else:
            break
    else:
        print("Could not fit resume to 2 Word pages after retries.", file=sys.stderr)
        sys.exit(1)

    print(f"Wrote {DOCX_PATH.relative_to(ROOT)}")

    try:
        export_pdf(DOCX_PATH, PDF_PATH)
        print(f"Wrote {PDF_PATH.relative_to(ROOT)}")
    except Exception as exc:  # noqa: BLE001
        print(f"PDF export failed ({exc}). Open Word and export PDF manually.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
