"""
Update index.html from the Word CV.

Word is the primary copy, so this rewrites only the sections that mirror it:
hero summary, impact highlights, experience cards, education, certificates and
tools. Site-only furniture (status panel, recommendations, FAQ, contact band,
easter egg) is left alone.

    python scripts/sync_site_from_docx.py
"""
from __future__ import annotations

import html
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resume_model import DOCX_PATH, ROOT, parse_docx, split_role_heading  # noqa: E402

HTML_PATH = ROOT / "index.html"

# Metrics, tools and product keywords worth emphasising on the site. Order
# matters: longer patterns first so "$8m+" wins before "$8m", and "Figma Make"
# wins before "Figma".
EMPHASIS = [
    r"\$\d[\d,.]*(?:bn|m|k)\+?",
    r"~\$\d[\d,.]*(?:bn|m|k)\+?",
    r"\bmulti-million-dollar\b",
    r"\bmulti-million-pound\b",
    r"\bmulti-million\b",
    r"\bbillions\b",
    r"\bsix figures\b",
    r"\bthousands of hours\b",
    r"\bhundreds of thousands of dollars\b",
    r"\b41 countries\b",
    r"\b12\+",
    r"\b20\+",
    r"\b10\+",
    r"\bthree cohorts\b",
    r"\b25 engineers\b",
    r"\bComirnaty \(COVID-19 vaccine\)",
    r"\bRegulatory Affairs and Operations\b",
    r"\bFDA, EMA and MHRA\b",
    r"\bAmazon 360\b",
    r"\bFigma Make\b",
    r"\bSnowflake\b",
    r"\bPower Platform\b",
    r"\bVeeva PromoMats\b",
    r"\bAutomation Anywhere\b",
    r"\bBeamex PCM\b",
    r"\bBeamex\b",
    r"\bcomputer system validation\b",
    r"\bPega\b",
    r"\bPendo\b",
    r"\bFigma\b",
    r"\bAlteryx\b",
    r"\bUiPath\b",
    r"\bSaaS\b",
    r"\bOKRs\b",
    r"\bRICE\b",
    r"\bMoSCoW\b",
    r"\bScrum\b",
    r"\bSAFe\b",
    r"\bGxP\b",
    r"\bCSV\b",
    r"\bUAT\b",
    r"\bFirst Class Honours\b",
    r"\bFirst Class\b",
]
_EMPHASIS_RE = re.compile("|".join(f"(?:{p})" for p in EMPHASIS))

# Industry filter tags used by the site's experience filter.
COMPANY_TAGS = {
    "Marsh": "insurance",
    "Kenvue": "consumer",
    "Johnson & Johnson": "consumer pharma",
    "Pfizer": "pharma",
    "GSK": "pharma",
}
COMPANY_META = {
    "Marsh": ("Insurance", "global insurance broker and consultancy"),
    "Kenvue": ("Consumer healthcare", "skin health, essential health"),
    "Johnson & Johnson": ("Consumer healthcare \u00b7 Pharmaceuticals \u00b7 MedTech", "global healthcare company"),
    "Pfizer": ("Pharmaceuticals", "biopharma &amp; vaccines"),
    "GSK": ("Pharmaceuticals", "biopharma"),
}


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def emphasise(text: str) -> str:
    """Wrap metrics/product names in <strong>; keep 'vibe coding' in italics."""
    out: list[str] = []
    cursor = 0
    for match in _EMPHASIS_RE.finditer(text):
        out.append(_with_italics(text[cursor : match.start()]))
        out.append(f"<strong>{esc(match.group(0))}</strong>")
        cursor = match.end()
    out.append(_with_italics(text[cursor:]))
    return "".join(out)


def _with_italics(text: str) -> str:
    parts: list[str] = []
    cursor = 0
    for match in re.finditer(r"vibe coding", text, re.I):
        parts.append(esc(text[cursor : match.start()]))
        parts.append(f"<em>{esc(match.group(0))}</em>")
        cursor = match.end()
    parts.append(esc(text[cursor:]))
    return "".join(parts)


def company_key(company: str) -> str:
    for key in COMPANY_TAGS:
        if key.lower() in company.lower():
            return key
    return ""


def replace_block(source: str, start_pat: str, end_pat: str, body: str, *, label: str) -> str:
    """Swap the text between an opening and closing marker."""
    match = re.search(f"({start_pat})(.*?)({end_pat})", source, re.DOTALL)
    if not match:
        raise SystemExit(f"Could not find the {label} block in index.html - aborting.")
    return source[: match.start()] + match.group(1) + body + match.group(3) + source[match.end() :]


def build_hero(model: dict) -> str:
    paragraphs = []
    for para in model["summary"]:
        paragraphs.append(
            "                <p class=\"hero__lede\">\n"
            f"                  {emphasise(para)}\n"
            "                </p>"
        )
    return "\n" + "\n".join(paragraphs) + "\n              "


def build_impact(model: dict) -> str:
    items = [f"            <li>{emphasise(item)}</li>" for item in model["impact"]]
    return "\n" + "\n".join(items) + "\n          "


def existing_role_tags(source: str) -> dict[str, str]:
    """Keep the decorative tool tags already on each experience card.

    They are presentation only and have no equivalent in the Word file, so they
    are carried over per role title rather than regenerated.
    """
    found: dict[str, str] = {}
    for card in re.finditer(r'<article class="xpCard".*?</article>', source, re.DOTALL):
        block = card.group(0)
        title = re.search(r'<h3 class="xpCard__title">(.*?)</h3>', block, re.DOTALL)
        tags = re.search(r'(<div class="tags"[^>]*>.*?</div>)', block, re.DOTALL)
        if title and tags:
            found[html.unescape(title.group(1)).strip()] = tags.group(1)
    return found


def build_experience(model: dict, kept_tags: dict[str, str]) -> str:
    cards = []
    for role in model["roles"]:
        parts = split_role_heading(role["heading"])
        key = company_key(parts["company"])
        tags = COMPANY_TAGS.get(key, "")
        industry, descriptor = COMPANY_META.get(key, ("", ""))
        dates = parts["dates"].replace(" - Present", " to present").replace(" - ", " to ")
        bullets = "\n".join(f"                  <li>{emphasise(b)}</li>" for b in role["bullets"])
        tag_block = kept_tags.get(parts["title"].strip(), "")
        tag_html = f"\n                {tag_block}" if tag_block else ""
        cards.append(
            f"""            <article class="xpCard" data-tags="{tags}">
              <div class="xpCard__body">
                <header class="xpCard__top">
                  <div class="xpCard__head">
                    <h3 class="xpCard__title">{esc(parts['title'])}</h3>
                    <div class="xpCard__org">
                      <span class="xpCard__orgName">{esc(parts['company'])}</span>
                      <span class="xpCard__dot" aria-hidden="true">\u2022</span>
                      <span class="xpCard__orgMeta">
                        <span class="xpCard__orgLine">
                          <span class="xpCard__orgIndustry">{industry}</span>
                          <span class="xpCard__orgSep" aria-hidden="true">\u00b7</span>
                          <span class="xpCard__orgDesc">{descriptor}</span>
                        </span>
                        <span class="xpCard__orgLoc">{esc(parts['location'])}</span>
                      </span>
                    </div>
                  </div>
                  <div class="xpCard__date">{esc(dates)}</div>
                </header>
                <ul class="bullets">
{bullets}
                </ul>{tag_html}
              </div>
            </article>"""
        )
    return "\n" + "\n\n".join(cards) + "\n          "


def build_education(model: dict) -> str:
    edu = model["education"]
    heading = edu["heading"]
    school, sep, rest = heading.partition(" - ")
    if not sep:
        school, _, rest = heading.partition("  |  ")
    degree, _, grade = rest.partition("  |  ")
    grade_main, _, grade_extra = grade.partition(", ")
    bullets = "\n".join(
        f"                <li>{emphasise(b)}</li>" for b in edu["bullets"]
    )
    grade_html = f"<strong>{esc(grade_main)}</strong>"
    if grade_extra:
        grade_html += (
            "\n                  <span class=\"eduChip__gradeSep\" aria-hidden=\"true\">\u00b7</span>"
            f"\n                  <span class=\"eduChip__gpa\">{esc(grade_extra)}</span>"
        )
    return f"""
            <div class="eduChip">
              <div class="eduChip__h">{esc(school)}</div>
              <div class="eduChip__meta">
                <div class="eduChip__degree">{esc(degree)}</div>
                <div class="eduChip__grade">
                  {grade_html}
                </div>
              </div>
              <ul class="eduChip__bullets" aria-label="Highlights">
{bullets}
              </ul>
            </div>
          """


def build_certificates(model: dict) -> str:
    certs: list[str] = []
    for entry in model["certifications"]:
        certs.extend(part.strip() for part in entry.split(",") if part.strip())
    items = [f"            <li><strong>{esc(c)}</strong></li>" for c in certs]
    return "\n" + "\n".join(items) + "\n          "


def build_tools(model: dict) -> str:
    groups = []
    for group in model["tools"]:
        slug = re.sub(r"[^a-z0-9]+", "-", group["label"].lower()).strip("-") or "tools"
        tags = "".join(
            f"<span class=\"tag\">{esc(item.strip())}</span>"
            for item in group["items"].split(",")
            if item.strip()
        )
        groups.append(
            f"""            <div class="toolGroup" role="group" aria-labelledby="toolbox-{slug}">
              <h3 class="toolGroup__h" id="toolbox-{slug}">{esc(group['label'])}</h3>
              <div class="tags" aria-label="{esc(group['label'])}">
                {tags}
              </div>
            </div>"""
        )
    return "\n" + "\n".join(groups) + "\n          "


def bump_timestamp(source: str) -> str:
    try:
        from zoneinfo import ZoneInfo

        now = datetime.now(ZoneInfo("Europe/London"))
    except Exception:  # noqa: BLE001 - Windows without tzdata
        now = datetime.now().astimezone()

    offset = now.utcoffset() or timedelta(0)
    hours = int(offset.total_seconds() // 3600)
    minutes = int(abs(offset.total_seconds()) % 3600 // 60)
    sign = "+" if hours >= 0 else "-"
    utc_label = f"UTC{sign}{abs(hours)}" + (f":{minutes:02d}" if minutes else "")
    display = f"{now.day} {now.strftime('%b %Y')}, {now.strftime('%H:%M')} UK ({now.tzname() or 'UK'}, {utc_label})"

    updated, count = re.subn(
        r'(<p class="siteFoot__updated">Last updated <time datetime=")[^"]*("[^>]*>)[^<]*(</time></p>)',
        rf"\g<1>{now.isoformat(timespec='seconds')}\g<2>{display}\g<3>",
        source,
        count=1,
    )
    if not count:
        print("Warning: could not find the footer timestamp to bump.", file=sys.stderr)
        return source
    print(f"Site last updated: {display}")
    return updated


def main() -> None:
    if not HTML_PATH.exists():
        raise SystemExit(f"Missing {HTML_PATH}")
    if not DOCX_PATH.exists():
        raise SystemExit(f"Missing {DOCX_PATH}")

    model = parse_docx(DOCX_PATH)
    if not model["roles"]:
        raise SystemExit("No roles parsed from the Word file - aborting.")

    source = HTML_PATH.read_text(encoding="utf-8")

    source = replace_block(
        source,
        r'<div class="hero__ledes">',
        r'</div>\s*\n\s*<div class="hero__chips"',
        build_hero(model),
        label="hero summary",
    )
    source = replace_block(
        source,
        r'<ul class="impactWins" aria-label="Impact highlights">',
        r"</ul>",
        build_impact(model),
        label="impact highlights",
    )
    source = replace_block(
        source,
        r'<div class="xpList" id="xpList">',
        r'</div>\s*\n\s*<p class="filterEmpty"',
        build_experience(model, existing_role_tags(source)),
        label="experience",
    )
    source = replace_block(
        source,
        r'<div class="eduRow" aria-label="Education">',
        r"</div>\s*\n\s*</section>",
        build_education(model),
        label="education",
    )
    source = replace_block(
        source,
        r'<ul class="bullets" aria-label="Certificates">',
        r"</ul>",
        build_certificates(model),
        label="certificates",
    )
    source = replace_block(
        source,
        r'<div class="toolGroups">',
        r"</div>\s*\n\s*</section>",
        build_tools(model),
        label="tools",
    )
    source = re.sub(
        r'(<a class="topbar__link" href="#toolbox-skills">)(.*?)(</a>)',
        r"\1Skills, tools &amp; platforms\3",
        source,
        count=1,
    )
    source = re.sub(
        r'(id="toolbox-skills"[^>]*>\s*<div class="sectionHead">\s*<h2 class="h2">)(.*?)(</h2>)',
        r"\1Skills, tools &amp; platforms\3",
        source,
        count=1,
        flags=re.S,
    )

    source = bump_timestamp(source)
    HTML_PATH.write_text(source, encoding="utf-8")
    print(f"Updated {HTML_PATH.relative_to(ROOT)} from the Word CV")


if __name__ == "__main__":
    main()
