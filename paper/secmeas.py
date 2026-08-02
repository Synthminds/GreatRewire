#!/usr/bin/env python3
"""Measure each Part of the paper against the submission's page limits.

The Forecasting the Future 2026 brief caps Section 1 at one page, Section 2 at
three, and asks for roughly five for Section 3. Those are limits on *sections*,
not on the document, so a page count does not answer the question. This locates
each "Part N" heading and reports the extent of each section in pages, counting
the fraction of the page each heading sits down.

Front matter (title, abstract, declarations) is reported but not scored: it was
agreed to count separately from Section 1. Section 3 is scored only against a
lower bound, since it is allowed to run over and the references sit inside it.

Usage:
    python paper/secmeas.py [PDF]     # defaults to texbuild/paper.pdf

Exit status is 0 whether or not the limits are met; read the last line. Requires
PyMuPDF, see requirements-paper.txt.
"""

import sys

import fitz

TOP, BOT = 61.0, 745.0  # text block, excluding running head and folio
H = BOT - TOP

# Scored limits, in pages. Section 3 carries a floor rather than a ceiling.
LIMITS = {"Section 1": 1.0, "Section 2": 3.0, "Section 3": 5.0}
SECTION_3_FLOOR = 4.4
TOLERANCE = 0.005  # a rounding allowance, well under one line

doc = fitz.open(sys.argv[1] if len(sys.argv) > 1 else "texbuild/paper.pdf")

# Position of each Part heading, as page index plus fraction down the text block.
heads: dict[str, float] = {}
for page_no, page in enumerate(doc):
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            text = "".join(s["text"] for s in line["spans"]).strip()
            for key, pattern in (("P1", "Part 1"), ("P2", "Part 2"), ("P3", "Part 3")):
                if key not in heads and text.startswith(pattern):
                    top = line["spans"][0]["bbox"][1]
                    heads[key] = page_no + max(0.0, min(1.0, (top - TOP) / H))

missing = [k for k in ("P1", "P2", "P3") if k not in heads]
if missing:
    sys.exit(f"could not locate heading(s): {', '.join(missing)}")

end = float(len(doc))
rows = [
    ("Front matter", 0.0, heads["P1"]),
    ("Section 1", heads["P1"], heads["P2"]),
    ("Section 2", heads["P2"], heads["P3"]),
    ("Section 3", heads["P3"], end),
]

ok = True
print(f"{'section':14}{'pages':>8}{'limit':>8}{'delta':>9}")
for name, start, stop in rows:
    span = stop - start
    limit = LIMITS.get(name)
    if limit is None:
        print(f"{name:14}{span:8.2f}{'--':>8}{'--':>9}")
        continue
    delta = span - limit
    if name == "Section 3":
        flag = "ok" if span >= SECTION_3_FLOOR else "OUT"
    else:
        flag = "ok" if delta <= TOLERANCE else "OVER"
    ok &= flag == "ok"
    print(f"{name:14}{span:8.2f}{limit:8.1f}{delta:+9.2f}  {flag}")

print(f"total pages: {len(doc)}")
print("SECTION LIMITS MET" if ok else "*** LIMITS NOT MET ***")
