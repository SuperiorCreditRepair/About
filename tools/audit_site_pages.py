#!/usr/bin/env python3
"""Editorial audit of the polished in-repo ChatGPT pages."""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audit_reports"
FILES = [
    ROOT / "ABOUT.md",
    ROOT / "CONTACT.md",
    ROOT / "HOMEBUYER.md",
    ROOT / "CREDIT-CLEANUP.md",
    ROOT / "site" / "consumer-credit-guide.html",
    ROOT / "site" / "review-credit-before-home-loan.html",
]

CHECKS = [
    ("hard_guarantee", re.compile(r"\bwe guarantee|guaranteed (score|approval|deletion|results?)\b", re.I)),
    ("ai_leakage", re.compile(r"\bas an AI|as a language model|ChatGPT(?!-Image)\b", re.I)),
    ("chatgpt_image_filename", re.compile(r"ChatGPT-Image", re.I)),
    ("placeholder", re.compile(r"TODO|FIXME|lorem ipsum|Replace this comment", re.I)),
    ("ssn_or_secret_ask", re.compile(r"social security number|full account number", re.I)),
    ("cta_form", re.compile(r"ff_landing|gohighlevel|contact form", re.I)),
    ("no_guarantee_disclaimer", re.compile(r"do not guarantee|cannot guarantee|no ethical credit service can guarantee", re.I)),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in FILES:
        text = path.read_text(encoding="utf-8", errors="replace")
        words = re.findall(r"[A-Za-z0-9']+", text)
        flags = []
        for name, pat in CHECKS:
            if pat.search(text):
                flags.append(name)
        rows.append(
            {
                "file": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "word_count": len(words),
                "flags": "|".join(flags) if flags else "",
            }
        )
    with (OUT / "site_page_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["file", "bytes", "word_count", "flags"])
        writer.writeheader()
        writer.writerows(rows)
    lines = ["# In-repo polished page audit", ""]
    for row in rows:
        lines.append(f"- `{row['file']}` — {row['word_count']} words — {row['flags'] or 'no flags'}")
    (OUT / "SITE_PAGE_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
