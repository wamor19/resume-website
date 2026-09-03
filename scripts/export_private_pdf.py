"""
Build a second copy of the CV that carries the phone number.

The published CV deliberately has no phone number on it: the site is public, so
anything in it is scrapeable. Applications are different - Workday and similar
forms want a phone, and their resume parsers use it to locate the contact block.

So the Word master stays phone-free and this script writes a parallel copy with
the number inserted into the contact line. The number and both generated files
live in `private/`, which is git-ignored and never part of the site build, so
the phone version cannot reach the web by accident.

The number is read from `private/phone.txt`. With no such file this is a no-op,
which is what keeps `sync_resume.py` working on a fresh clone.

    python scripts/export_private_pdf.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import export_pdf  # noqa: E402
from format_resume_docx import (  # noqa: E402
    WRAP_SAFETY_PT,
    contact_parts,
    fit_and_save,
    text_width_pt,
    usable_width_pt,
)
from resume_model import DOCX_PATH, ROOT, SEP, parse_docx  # noqa: E402

PRIVATE_DIR = ROOT / "private"
PHONE_FILE = PRIVATE_DIR / "phone.txt"
# Same filename as the public copy: this is the one that gets attached to an
# application, so it should not arrive called "with phone".
PRIVATE_DOCX = PRIVATE_DIR / DOCX_PATH.name
PRIVATE_PDF = PRIVATE_DIR / f"{DOCX_PATH.stem}.pdf"


def read_phone() -> str | None:
    if not PHONE_FILE.exists():
        return None
    return PHONE_FILE.read_text(encoding="utf-8").strip() or None


def with_phone(headline: str, phone: str) -> str:
    """Put the phone immediately before the email, where parsers expect it."""
    parts = [part.strip() for part in headline.split("|") if part.strip()]
    if phone not in parts:
        email = next((i for i, part in enumerate(parts) if "@" in part), len(parts))
        parts.insert(email, phone)
    return SEP.join(parts)


def main() -> None:
    phone = read_phone()
    if phone is None:
        print(f"No {PHONE_FILE.relative_to(ROOT)} - skipping the phone copy.")
        return

    if not DOCX_PATH.exists():
        raise SystemExit(f"Missing {DOCX_PATH}")

    model = parse_docx(DOCX_PATH)
    model["headline"] = with_phone(model["headline"], phone)

    PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    fit = fit_and_save(model, PRIVATE_DOCX)

    # The phone makes the contact line longer, and that line must not wrap.
    text = SEP.join(part for part, _ in contact_parts(model["headline"]))
    width = text_width_pt(text, fit.contact_pt)
    usable = usable_width_pt(fit) - WRAP_SAFETY_PT
    if width is not None and width > usable:
        print(
            f"  note: contact line is {width - usable:.0f}pt too wide at "
            f"{fit.contact_pt}pt and will wrap onto a second line.",
            file=sys.stderr,
        )

    if phone not in parse_docx(PRIVATE_DOCX)["headline"]:
        raise SystemExit("The phone copy came back without the number - not exporting it.")

    export_pdf.export(docx=PRIVATE_DOCX, pdf=PRIVATE_PDF, keep_history=False)
    print(f"Wrote {PRIVATE_PDF.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
