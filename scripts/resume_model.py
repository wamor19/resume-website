"""
Read the Word CV into a structured model.

The Word file is the primary copy of the CV. Everything else (PDF, website) is
built from this model, so the parser is deliberately forgiving: hand-editing in
Word tends to merge a section heading onto the end of the previous bullet, style
a role heading as a list item, or leave stray empty paragraphs behind.
"""
from __future__ import annotations

import re
from pathlib import Path

from docx import Document

ROOT = Path(__file__).resolve().parents[1]
DOCX_PATH = ROOT / "assets" / "files" / "Resume (William Amor).docx"

NAME = "William Amor"

SECTION_SUMMARY = "PROFESSIONAL SUMMARY"
SECTION_IMPACT = "IMPACT HIGHLIGHTS"
SECTION_EXPERIENCE = "EXPERIENCE"
SECTION_EDUCATION = "EDUCATION"
SECTION_CERTIFICATIONS = "CERTIFICATIONS"
SECTION_TOOLS = "SKILLS, TOOLS & PLATFORMS"

# Order defines the order sections are written back out.
SECTIONS = (
    SECTION_SUMMARY,
    SECTION_IMPACT,
    SECTION_EXPERIENCE,
    SECTION_EDUCATION,
    SECTION_CERTIFICATIONS,
    SECTION_TOOLS,
)
_HEADING_ALIASES = {
    "SKILLS": SECTION_TOOLS,
    "SKILLS TOOLS PLATFORMS": SECTION_TOOLS,
    "SKILLS, TOOLS & PLATFORMS": SECTION_TOOLS,
    "TOOLS AND PLATFORMS": SECTION_TOOLS,
    "TOOLS & PLATFORMS": SECTION_TOOLS,
    "CERTIFICATES": SECTION_CERTIFICATIONS,
    "SUMMARY": SECTION_SUMMARY,
}

SEP = "  |  "

_ASCII_FOLD = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201a": ",",
    "\u201c": '"',
    "\u201d": '"',
    "\u201e": '"',
    "\u2013": "-",
    "\u2014": "-",
    "\u2026": "...",
    "\u2011": "-",
    "\u00a0": " ",
    "\u2022": "-",
    "\u00b7": "|",
}

# A heading pulled onto the end of a sentence, e.g. "...resolution.EDUCATION".
_MERGED_HEADING_RE = re.compile(
    r"(?<=[a-z\)\.\!\?])(" + "|".join(re.escape(h) for h in (*SECTIONS, "SKILLS", "CERTIFICATES")) + r")\s*$"
)

_DATE_RANGE_RE = re.compile(
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4}\s*[-\u2013]\s*"
    r"(?:Present|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{4})",
    re.I,
)


def ascii_fold(text: str) -> str:
    for src, dst in _ASCII_FOLD.items():
        text = text.replace(src, dst)
    return text


def clean(text: str) -> str:
    return re.sub(r"[ \t]+", " ", ascii_fold(text)).strip()


def normalise_separators(text: str) -> str:
    """Collapse any pipe spacing to the canonical two-space form."""
    return re.sub(r"\s*\|\s*", SEP, text)


def _norm_heading(text: str) -> str:
    """Uppercase, strip punctuation (except &), collapse spaces."""
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z& ]", "", text.upper())).strip()


def _canonical_heading(text: str) -> str | None:
    key = _norm_heading(text)
    for section in SECTIONS:
        if _norm_heading(section) == key:
            return section
    for alias, section in _HEADING_ALIASES.items():
        if _norm_heading(alias) == key:
            return section
    return None


def _is_bullet_style(paragraph) -> bool:
    return paragraph.style.name in {"List Bullet", "List Paragraph", "List Number"}


def _is_role_line(text: str) -> bool:
    return "|" in text and bool(_DATE_RANGE_RE.search(text))


def _split_merged_heading(text: str) -> tuple[str, str | None]:
    """Return (body, trailing heading) for '...sentence.EDUCATION' style edits."""
    match = _MERGED_HEADING_RE.search(text)
    if not match:
        return text, None
    body = text[: match.start()].strip()
    return body, _canonical_heading(match.group(1))


def _flatten(doc: Document) -> list[tuple[str, str, bool]]:
    """Yield (kind, text, bold) where kind is heading | role | bullet | text."""
    items: list[tuple[str, str, bool]] = []

    def push(raw: str, *, bullet: bool, bold: bool) -> None:
        text = clean(raw)
        if not text:
            return
        body, trailing = _split_merged_heading(text)
        heading = _canonical_heading(body) if not bullet else None
        if heading and not trailing:
            items.append(("heading", heading, True))
            return
        if body:
            if _is_role_line(body):
                items.append(("role", normalise_separators(body), True))
            else:
                items.append(("bullet" if bullet else "text", body, bold))
        if trailing:
            items.append(("heading", trailing, True))

    for paragraph in doc.paragraphs:
        if not paragraph.text.strip():
            continue
        bold = any(run.bold for run in paragraph.runs)
        push(paragraph.text, bullet=_is_bullet_style(paragraph), bold=bold)

    return items


def parse_docx(path: Path = DOCX_PATH) -> dict:
    doc = Document(str(path))
    items = _flatten(doc)

    model: dict = {
        "name": NAME,
        "headline": "",
        "summary": [],
        "impact": [],
        "roles": [],
        "education": {"heading": "", "bullets": []},
        "certifications": [],
        "tools": [],
    }

    # Everything before the first section heading is the name/contact block.
    section: str | None = None
    for kind, text, _bold in items:
        if kind == "heading":
            section = text
            continue

        if section is None:
            # Name line is rebuilt from constants; contact line is regenerated
            # with live hyperlinks, so only the headline is worth keeping.
            if text != NAME and not model["headline"]:
                model["headline"] = text
            continue

        if section == SECTION_SUMMARY:
            model["summary"].append(text)

        elif section == SECTION_IMPACT:
            model["impact"].append(text)

        elif section == SECTION_EXPERIENCE:
            if kind == "role":
                model["roles"].append({"heading": text, "bullets": []})
            elif model["roles"]:
                model["roles"][-1]["bullets"].append(text)

        elif section == SECTION_EDUCATION:
            if kind == "bullet" or model["education"]["heading"]:
                model["education"]["bullets"].append(text)
            else:
                model["education"]["heading"] = normalise_separators(text)

        elif section == SECTION_CERTIFICATIONS:
            model["certifications"].append(text)

        elif section == SECTION_TOOLS:
            label, _, body = text.partition(":")
            if body.strip():
                model["tools"].append({"label": label.strip(), "items": body.strip()})
            else:
                model["tools"].append({"label": "", "items": text})

    return model


def split_role_heading(heading: str) -> dict:
    """'Title  |  Company  |  Location  |  Dates' -> parts (tolerates missing bits)."""
    parts = [p.strip() for p in heading.split("|") if p.strip()]
    dates = ""
    if parts and _DATE_RANGE_RE.search(parts[-1]):
        dates = parts.pop()
    title = parts.pop(0) if parts else ""
    company = parts.pop(0) if parts else ""
    location = parts.pop(0) if parts else ""
    return {
        "title": title,
        "company": company,
        "location": location,
        "dates": dates,
        "extra": parts,
    }


if __name__ == "__main__":
    data = parse_docx()
    print(f"headline: {data['headline']}")
    print(f"summary paragraphs: {len(data['summary'])}")
    print(f"impact bullets: {len(data['impact'])}")
    print(f"roles: {len(data['roles'])}")
    for role in data["roles"]:
        parts = split_role_heading(role["heading"])
        print(f"  - {parts['title']} @ {parts['company']} ({parts['dates']}): {len(role['bullets'])} bullets")
    print(f"education bullets: {len(data['education']['bullets'])}")
    print(f"certifications: {data['certifications']}")
    print(f"tool groups: {[t['label'] for t in data['tools']]}")
