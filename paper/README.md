# Paper build

How the published PDF was produced. **The manuscript source is not distributed
here.** These files are provenance, not a pipeline a third party can run
unchanged: `build_tex.py` needs a manuscript, and without one it exits with a
message saying so. What you can run standalone is `annotate_flags.py` and
`secmeas.py`, both of which work off artifacts already in this repository.

| file | what it is |
| --- | --- |
| `the-great-rewiring-shields-2026.pdf` | the published paper, ten pages |
| `build_tex.py` | markdown to PDF via pandoc and pdflatex |
| `annotate_flags.py` | adds country flags to the Exhibit X2 multigraph |
| `secmeas.py` | measures each section against the submission page limits |
| `flags/` | 31 Twemoji PNGs, CC BY 4.0 |

## Requirements

`pandoc`, a TeX installation with `txfonts` and `microtype` (TeX Live 2023 or
later covers this), and `pip install -r ../requirements-paper.txt` for the
PyMuPDF-based tools. These are deliberately kept out of `requirements.txt` so the
analysis runtime and CI stay unchanged.

## Building

```sh
GRW_SOURCE=/path/to/manuscript.md python paper/build_tex.py 10
python paper/secmeas.py paper/texbuild/paper.pdf
```

`build_tex.py` copies `figures/*.pdf` into its build directory, converts the
markdown with pandoc, patches the LaTeX by hand for maths and floats, then runs
`latexmk`. Set `GRW_WORKDIR` to build somewhere other than `paper/`.

### Fit dials

Page count is controlled by four environment variables. The defaults in the
script are the values that produced the published PDF; changing any of them
changes the pagination. Reach for them in this order:

| dial | default | effect |
| --- | --- | --- |
| `LEAD` | `0.97` | `\linespread`; the finest-grained control |
| `MARG` | `1.0in` | left and right margins |
| `VMAR` | `0.95in,0.9in` | top and bottom margins |
| `P3` | `footnotesize` | type size for Part 3, the appendix |

`secmeas.py` reports each section's extent in pages by locating the Part
headings, which is how the submission's per-section limits were checked.

### Exhibit X2 is pinned, and why

X1, X3 and X4 float on `[!ht]`. X2 is placed with `[H]` followed by
`\clearpage`, because it is meant to fill the foot of its page with the next
section starting clean overhead, and a float cannot express that. Measured
alternatives on the published text: `[!ht]` slid it to the following page and
pushed Part 2 to 3.50 pages; `[H]` without the `\clearpage` left a hole at the
foot of the page and gave the same 3.50. Its width is capped at 0.78 of the text
block for the same reason: at 0.80 the block no longer fits below the preceding
section and the whole figure jumps a page.

## Flags

```sh
python paper/annotate_flags.py --verify paper/reference.pdf
```

`analysis/20_multigraph.py` renders Exhibit X2 without flags.
`annotate_flags.py` adds one beside every ISO3 label on the ring and every row of
the chokepoint legend, and appends the Twemoji attribution to the figure's own
source line so the credit travels with the figure.

Placement is derived from the figure rather than hard-coded: legend flags sit
2.0 pt right of each `NN% ISO` span, ring flags sit 12.0 pt outward from the
label centre along the radius from the ring's centroid. The partition inset also
carries ISO3 labels, at a smaller size, and is excluded by keeping only the modal
label size.

**On reproduction, precisely:** re-running the script against the unflagged
figure places all 37 flags, with a worst coordinate difference of 1.30 pt and a
mean of 0.47 pt against the published rendering — visually indistinguishable on
a 6.4 pt flag, but not identical. The original placed a few labels off their own
geometry rather than off a common radius. `figures/x1_multigraph.pdf` therefore
holds the published rendering, not this script's output.

Twemoji is © Twitter, Inc. and other contributors, licensed CC BY 4.0.
