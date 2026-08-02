#!/usr/bin/env python3
"""Annotate the strategic-layer multigraph with country flags.

Exhibit X2 is rendered without flags by ``analysis/20_multigraph.py``. The
published figure adds a small flag beside every ISO3 node label on the ring and
beside every share row in the chokepoint legend, so a reader can place the
countries without decoding three-letter codes. The flags are Twemoji, which is
CC BY 4.0 and therefore carries an attribution obligation; this script appends
that attribution to the figure's own source line rather than spending body space
on it.

Placement is derived from the figure, not hard-coded:

* Legend rows are the ``NN% ISO`` spans. A flag goes ``LEGEND_DX`` to the right
  of the span, vertically centred on it.
* Node labels are the bare ISO3 spans arranged on a ring. A flag goes
  ``NODE_RADIAL`` points outward from the label centre, along the radius from
  the ring's centroid, so flags sit outside the ring rather than over the edges.

Both offsets were recovered by measuring the published figure. They reproduce its
37 placements closely but not exactly: worst coordinate difference 1.30 pt, mean
0.47 pt, against a 6.4 pt flag. The residual is because the original placed a few
labels off their own geometry rather than off a common radius. The output is
visually indistinguishable from the published figure; it is not byte-identical to
it, and ``figures/x1_multigraph.pdf`` holds the published rendering rather than
this script's output.

Usage:
    python paper/annotate_flags.py                       # figures/ in place
    python paper/annotate_flags.py --out /tmp/out.pdf
    python paper/annotate_flags.py --verify REFERENCE.pdf

Requires PyMuPDF; see requirements-paper.txt.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import sys

import fitz

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent

FLAGS = HERE / "flags"
FIGURE = REPO / "figures" / "x1_multigraph.pdf"

FLAG_SIZE = 6.4  # points, matches the 6pt label cap-height closely enough to read
LEGEND_DX = 2.0  # gap between the end of a legend row and its flag
NODE_RADIAL = 12.0  # outward offset from a ring label's centre

ATTRIBUTION = "  Flag icons: Twemoji, CC BY 4.0."

ISO3 = re.compile(r"^[A-Z]{3}$")
LEGEND_ROW = re.compile(r"^\d+%\s+([A-Z]{3})$")


def spans(page: fitz.Page) -> list[tuple[str, fitz.Rect, float]]:
    """Every non-empty text span on the page, with its box and size."""
    out = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            for span in line["spans"]:
                text = span["text"].strip()
                if text:
                    out.append((text, fitz.Rect(span["bbox"]), span["size"]))
    return out


def placements(page: fitz.Page) -> list[tuple[str, fitz.Rect]]:
    """Work out where each flag belongs. Returns (ISO3, target rect) pairs."""
    found = spans(page)

    legend = []
    for text, box, _size in found:
        match = LEGEND_ROW.match(text)
        if match:
            x0 = box.x1 + LEGEND_DX
            cy = (box.y0 + box.y1) / 2
            legend.append(
                (
                    match.group(1),
                    fitz.Rect(x0, cy - FLAG_SIZE / 2, x0 + FLAG_SIZE, cy + FLAG_SIZE / 2),
                )
            )

    # The partition inset also carries ISO3 labels, at a smaller size than the ring.
    # Rather than hard-code either size, keep only the modal one: the ring is by far
    # the largest group of ISO3 labels in the figure.
    candidates = [(t, b, round(s, 2)) for t, b, s in found if ISO3.match(t)]
    if not candidates:
        return legend
    sizes = [s for _t, _b, s in candidates]
    ring_size = max(set(sizes), key=sizes.count)
    nodes = [(t, b) for t, b, s in candidates if s == ring_size]

    # The ring's centre is the centroid of its own labels, so this holds up if the
    # figure is ever re-laid-out at a different size or with a different node set.
    cx = sum((b.x0 + b.x1) / 2 for _t, b in nodes) / len(nodes)
    cy = sum((b.y0 + b.y1) / 2 for _t, b in nodes) / len(nodes)

    ring = []
    for text, box in nodes:
        mx, my = (box.x0 + box.x1) / 2, (box.y0 + box.y1) / 2
        dx, dy = mx - cx, my - cy
        norm = (dx * dx + dy * dy) ** 0.5 or 1.0
        px = mx + NODE_RADIAL * dx / norm
        py = my + NODE_RADIAL * dy / norm
        ring.append(
            (
                text,
                fitz.Rect(
                    px - FLAG_SIZE / 2, py - FLAG_SIZE / 2, px + FLAG_SIZE / 2, py + FLAG_SIZE / 2
                ),
            )
        )
    return legend + ring


def annotate(src: pathlib.Path, dst: pathlib.Path) -> int:
    doc = fitz.open(src)
    page = doc[0]

    placed = 0
    missing = set()
    for iso, rect in placements(page):
        png = FLAGS / f"{iso}.png"
        if not png.exists():
            missing.add(iso)
            continue
        page.insert_image(rect, filename=str(png), keep_proportion=False)
        placed += 1

    # The CC BY attribution rides on the figure's existing source line, so it
    # travels with the figure wherever the figure is reused.
    for text, box, size in spans(page):
        if text.startswith("Source:") and "Twemoji" not in text:
            page.add_redact_annot(
                box, text=text + ATTRIBUTION, fontname="helv", fontsize=size, align=0
            )
            page.apply_redactions()
            break

    doc.save(dst)
    doc.close()
    if missing:
        print(f"no flag asset for: {', '.join(sorted(missing))}", file=sys.stderr)
    return placed


def verify(produced: pathlib.Path, reference: pathlib.Path) -> bool:
    """Compare flag placements against a reference rendering."""
    a = sorted(
        tuple(round(v, 1) for v in im["bbox"]) for im in fitz.open(produced)[0].get_image_info()
    )
    b = sorted(
        tuple(round(v, 1) for v in im["bbox"]) for im in fitz.open(reference)[0].get_image_info()
    )
    if len(a) != len(b):
        print(f"placement count differs: {len(a)} vs {len(b)}")
        return False
    diffs = [max(abs(p - q) for p, q in zip(x, y)) for x, y in zip(a, b)]
    worst = max(diffs, default=0.0)
    mean = sum(diffs) / len(diffs) if diffs else 0.0
    print(
        f"{len(a)} placements, worst {worst:.2f} pt, mean {mean:.2f} pt "
        f"(flag is {FLAG_SIZE} pt)"
    )
    # Tolerance, not equality: see the module docstring on why the reproduction is
    # close rather than exact. A regression past this would mean the rule drifted.
    return worst < 2.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", type=pathlib.Path, default=FIGURE)
    ap.add_argument(
        "--out", type=pathlib.Path, default=None, help="output path; defaults to overwriting --src"
    )
    ap.add_argument(
        "--verify",
        type=pathlib.Path,
        default=None,
        help="compare placements against this reference PDF",
    )
    args = ap.parse_args()

    out = args.out or args.src
    tmp = out.with_suffix(".tmp.pdf")
    placed = annotate(args.src, tmp)
    print(f"placed {placed} flags")

    ok = True
    if args.verify:
        ok = verify(tmp, args.verify)

    tmp.replace(out)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
