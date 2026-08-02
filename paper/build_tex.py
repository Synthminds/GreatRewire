#!/usr/bin/env python3
"""Typeset The Great Rewiring with LaTeX.

Markdown -> pandoc -> hand-fixed LaTeX -> pdflatex. Chosen over an HTML/print
route for native maths, real float placement for the four wide exhibits,
microtype, and proper hyphenation.

Text and matched maths are txfonts (Times). An earlier revision used mathptmx;
it was replaced because its maths face did not match the text face.

The manuscript source is not distributed with this repository, so this script
documents how the published PDF was produced rather than offering a pipeline a
third party can run unchanged. Point GRW_SOURCE at a manuscript to build one.

Requires: pandoc, pdflatex/latexmk with txfonts and microtype, and the fonts
TeX Live ships by default. Install the Python side with requirements-paper.txt.

Usage:
    python paper/build_tex.py [POINT_SIZE]        # default 10
    GRW_SOURCE=/path/to/manuscript.md python paper/build_tex.py

Dials, in the order to reach for them when the page count is wrong: LEAD, then
MARG, then VMAR, then P3. The defaults below are the values that produced the
published ten-page PDF; changing any of them changes the pagination.
"""

import os
import pathlib
import re
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent

# GRW_WORKDIR lets independent reviewers build from their own copy of the
# source without colliding on one build directory.
SP = pathlib.Path(os.environ.get("GRW_WORKDIR", HERE))
FIGDIR = pathlib.Path(os.environ.get("GRW_FIGDIR", REPO / "figures"))
SOURCE = pathlib.Path(os.environ.get("GRW_SOURCE", SP / "the-great-rewiring-REWRITTEN.md"))
BUILD = SP / "texbuild"
PT = sys.argv[1] if len(sys.argv) > 1 else "10"

# Defaults reproduce the published PDF. See the module docstring.
LEAD = os.environ.get("LEAD", "0.97")  # \linespread
MARG = os.environ.get("MARG", "1.0in")  # left/right margin
VMAR = os.environ.get("VMAR", "0.95in,0.9in")  # top,bottom margin
P3 = os.environ.get("P3", "footnotesize")  # type size for Part 3

if not SOURCE.exists():
    sys.exit(
        f"manuscript not found: {SOURCE}\n"
        "The manuscript source is not distributed with this repository. Set "
        "GRW_SOURCE to a markdown manuscript to build one."
    )

BUILD.mkdir(exist_ok=True)
for f in FIGDIR.glob("*.pdf"):
    shutil.copy(f, BUILD / f.name)

src = SOURCE.read_text()

# ---------------- front matter -----------------------------------------------
body_md = src.split("---", 1)[1]
m = re.search(r"##\s*Abstract\s*(.*?)\n---\n", body_md, re.S)
abstract_md, body_md = m.group(1), body_md[m.end() :]
repl = re.search(r"\*\*Replication\.\*\*(.*?)\n", abstract_md).group(1).strip()
decl = re.search(r"\*\*Declaration of AI use\.\*\*(.*?)$", abstract_md, re.S).group(1).strip()
abstract_body = abstract_md.split("**Replication.**")[0].strip()


def pandoc(md: str) -> str:
    return subprocess.run(
        ["pandoc", "--from=markdown", "--to=latex", "--wrap=preserve"],
        input=md,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


body = pandoc(body_md)
abstract_tex = pandoc(abstract_body)
repl_tex = pandoc(repl).strip()
decl_tex = pandoc(decl).strip()


# ---------------- Unicode -> LaTeX ------------------------------------------
# pdflatex cannot set the maths characters the markdown carries in prose.
# Compound forms are mapped before single glyphs so subscripts bind correctly.
UNI = [
    ("10\u207b\u1da0", r"$10^{-F}$"),
    ("\u03a3\u2096", r"$\sum_k$"),
    ("e\u1d62\u2c7c", r"$e_{ij}$"),
    ("w\u1d62", r"$w_i$"),
    ("w\u2c7c", r"$w_j$"),
    ("x\u1d62", r"$x_i$"),
    ("x\u2c7c", r"$x_j$"),
    ("\u03b1\u2080", r"$\alpha_0$"),
    ("\u03b2\u2080", r"$\beta_0$"),
    ("log\u2081\u2080", r"$\log_{10}$"),
    ("q\u221e", r"$q_\infty$"),
    ("R\u00b2", r"$R^2$"),
    ("ay\u00b2", r"$ay^2$"),
    ("\u03b1", r"$\alpha$"),
    ("\u03b2", r"$\beta$"),
    ("\u03ba", r"$\kappa$"),
    ("\u03bb", r"$\lambda$"),
    ("\u0393", r"$\Gamma$"),
    ("\u03a3", r"$\Sigma$"),
    ("\u00d7", r"$\times$"),
    ("\u2212", r"$-$"),
    ("\u00b7", r"$\cdot$"),
    ("\u2261", r"$\equiv$"),
    ("\u2248", r"$\approx$"),
    ("\u2265", r"$\geq$"),
    ("\u2264", r"$\leq$"),
    ("\u00b1", r"$\pm$"),
    ("\u221e", r"$\infty$"),
    ("\u2192", r"$\rightarrow$"),
    ("\u00a7", r"\S{}"),
    ("\u2081", r"$_1$"),
    ("\u2080", r"$_0$"),
    ("\u1d62", r"$_i$"),
    ("\u2c7c", r"$_j$"),
]


def de_unicode(s):
    for a, b in UNI:
        s = s.replace(a, b)
    return s


# ---------------- exhibits: quote blocks -> figure floats --------------------
# Exhibits are numbered in order of first appearance, so the label no longer
# matches the figure file's own name.
FIG = {"X1": "x2_divergence", "X2": "x1_multigraph", "X3": "x4_validation", "X4": "x3_envelope"}
# Wide landscape figures. Width is chosen per aspect so no float exceeds ~0.45
# of the text block, which keeps LaTeX from deferring them to a float page.
WIDTH = {"X1": 0.72, "X2": 0.78, "X3": 0.98, "X4": 0.58}


def to_float(mt):
    block = mt.group(0)
    tag = re.search(r"Exhibit\s+(X\d)", block)
    if not tag:
        return block
    key = tag.group(1)
    inner = re.sub(r"\\(begin|end)\{quote\}", "", block).strip()
    # the rendered figure carries its own source line, as in the reference draft
    inner = re.sub(r"\\emph\{Source:.*?\}\s*$", "", inner, flags=re.S).strip()
    cap = inner.replace(r"\textbf{Exhibit " + key + ".}", "").strip()
    # All four exhibits float on [!tb], top or bottom of a page. An earlier
    # revision pinned X2 with [H] plus a \clearpage so it would fill the foot of
    # its page; that was right while Part 2 opened mid-page, but once every Part
    # opens at a page top the forced break costs a whole page and pushes Part 2
    # over its three-page limit. [!ht] on the others left roughly 190pt empty at
    # one page foot for the same reason. Letting LaTeX place all four recovers
    # the page and holds Part 2 at exactly 3.00.
    placement = "[!tb]"
    tail = ""
    return (
        f"\\begin{{figure}}{placement}\n\\centering\n"
        f"\\includegraphics[width={WIDTH[key]}\\textwidth]{{{FIG[key]}.pdf}}\n"
        f"\\caption*{{\\textbf{{Exhibit {key}.}} {cap}}}\n"
        f"\\label{{fig:{key.lower()}}}\n\\end{{figure}}\n" + tail
    )


body = re.sub(r"\\begin\{quote\}.*?\\end\{quote\}", to_float, body, flags=re.S)

# ---------------- equations: verbatim -> real display math -------------------
EQS = [
    r"""\begin{equation*}
x_i \equiv \frac{w_i}{\sum_{k=1}^{N} w_k / N},
\qquad
P_L[x_i,x_j] = \frac{\alpha\, x_i x_j}{1+\beta\, x_i x_j},
\qquad
e_{ij} = 10^{-F}\cdot\min(w_i,w_j),
\qquad
F \sim \Gamma(6.5571,\, 0.5794)
\end{equation*}""",
    r"""\begin{equation*}
y \equiv \log_{10}\!\left(\frac{e_{ij}}{w_i+w_j}\right),
\qquad
P_D[x_i,x_j] =
\begin{cases}
10^{\,ay^2+by+c}, & y \geq -10,\\[2pt]
0.36, & \text{otherwise.}
\end{cases}
\end{equation*}""",
]
_n = [0]


def swap_eq(mt):
    out = EQS[_n[0]] if _n[0] < len(EQS) else mt.group(0)
    _n[0] += 1
    return out


body = re.sub(r"\\begin\{verbatim\}.*?\\end\{verbatim\}", swap_eq, body, flags=re.S)


# ---------------- tables: longtable -> booktabs table float ------------------
def to_table(mt):
    """pandoc longtable -> booktabs table float.

    The header lives between \\toprule and \\midrule. pandoc wraps long header
    cells in minipages, so those must be stripped before splitting on &.
    """
    src = mt.group(0)
    head_raw = re.search(r"\\toprule.*?\n(.*?)\\midrule", src, re.S)
    head_raw = head_raw.group(1) if head_raw else ""
    head_raw = re.sub(
        r"\\begin\{minipage\}[^\n]*|\\end\{minipage\}|\\noalign\{\}|\\raggedright", " ", head_raw
    )
    head = [c.strip() for c in head_raw.replace("\\\\", "").split("&")]

    tail = src.split("\\endhead", 1)[-1]
    data = []
    for ln in tail.split("\n"):
        ln = ln.strip()
        if not ln.endswith("\\\\") or "&" not in ln:
            continue
        data.append([c.strip() for c in ln[:-2].split("&")])

    if not data:
        return src
    ncol = max(len(r) for r in data)
    if len(head) != ncol or not any(head):
        head = [""] * ncol
    align = "l" + "r" * (ncol - 1)
    out = [
        "\\begin{table}[htbp]",
        "\\centering\\small",
        "\\begin{tabular}{%s}" % align,
        "\\toprule",
    ]
    if any(h for h in head):
        out += [" & ".join("\\textbf{%s}" % h for h in head) + " \\\\", "\\midrule"]
    out += [" & ".join(r) + " \\\\" for r in data]
    out += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    return "\n".join(out)


body = re.sub(r"\\begin\{longtable\}.*?\\end\{longtable\}", to_table, body, flags=re.S)


# table captions in the source are italic paragraphs; attach them to the float
def attach_caption(mt):
    tbl, cap = mt.group(1), mt.group(2).strip()
    return tbl.replace("\\end{table}", f"\\caption*{{{cap}}}\n\\end{{table}}")


body = re.sub(
    r"(\\begin\{table\}.*?\\end\{table\})\s*\n\\emph\{(Table B\d\..*?)\}",
    attach_caption,
    body,
    flags=re.S,
)

# ---------------- headings ---------------------------------------------------
body = re.sub(r"\\section\{Part (\d)([^}]*)\}", r"\\section*{Part \1\2}", body)
body = body.replace("\\subsection{", "\\subsection*{").replace(
    "\\subsubsection{", "\\subsubsection*{"
)

# A float must not drift out of the Part that cites it.
# Each Part opens on a fresh page, so the section boundaries a reviewer counts
# against the per-section page limits are visible rather than mid-page.
body = re.sub(r"(?=\\section\*\{Part [123])", "\\\\FloatBarrier\\\\clearpage\n", body)
body = re.sub(r"(?=\\subsection\*\{F\. References)", "\\\\FloatBarrier\n", body)

# Part 3 is the technical appendix and is set a size down, which is worth most
# of a page. The group is closed at the end of the document body.
# pandoc wraps the heading in \hypertarget{..}{..}, so anchor on the whole line.
body, _k = re.subn(
    r"(\\section\*\{Part 3[^\n]*\n)", lambda m: m.group(1) + "{\\" + P3 + "\n", body, count=1
)
assert _k == 1, "Part 3 heading not found; the \\small group would be unbalanced"
body = body.rstrip() + "\n\\par}\n"

# references
# references.txt sits beside the manuscript, not in the build directory, so a
# reviewer pointing GRW_SOURCE elsewhere picks up that copy rather than this one.
refs = (SOURCE.parent / "references.txt").read_text().strip().split("\n")
ref_items = "\n".join(
    "\\item %s" % r.split("] ", 1)[1].replace("&", "\\&").replace("_", "\\_") for r in refs
)
# 38 entries set two-up at footnotesize, which is what buys the reference list
# back from a page and a half to two thirds of one. enumitem numbers them, so
# the label sits inside the column instead of hanging into the gutter.
ref_block = (
    "\\begin{multicols}{2}\\footnotesize\n"
    "\\begin{enumerate}[label={[\\arabic*]},leftmargin=*,labelsep=3pt,"
    "itemsep=1.4pt,parsep=0pt,topsep=2pt,align=left]\n"
    + ref_items
    + "\n\\end{enumerate}\n\\end{multicols}"
)
# pandoc escapes the brackets, so the placeholder contains nested braces;
# match through to the closing ".)}" rather than the first "}".
body = re.sub(
    r"\\emph\{\(Unchanged from the submitted draft.*?\.\)\}", lambda _m: ref_block, body, flags=re.S
)
body = body.replace("@@REFS@@", ref_block)

body = de_unicode(body)
abstract_tex = de_unicode(abstract_tex)
repl_tex = de_unicode(repl_tex)
decl_tex = de_unicode(decl_tex)

PRE = (
    r"""\documentclass[@@PT@@pt,letterpaper,oneside]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}                  % must precede txfonts
\usepackage{txfonts}                  % Times text with a matched Times maths
% amssymb is deliberately absent: txfonts already carries the AMS symbol set.

\usepackage[letterpaper,top=@@VT@@,bottom=@@VB@@,left=@@M@@,right=@@M@@,
            headheight=12pt,headsep=15pt,footskip=20pt]{geometry}

\usepackage[activate={true,nocompatibility},final,protrusion=true,expansion=true,
            factor=1100,stretch=15,shrink=15,kerning=true,spacing=true,
            tracking=true]{microtype}
\SetTracking{encoding={*},shape=sc}{40}   % open the small-caps running head

\usepackage{graphicx}
\usepackage{booktabs,array}
\usepackage{multicol}
\usepackage{float}
\usepackage{placeins}
\usepackage{fancyhdr}
\usepackage[font=small,labelfont=bf,labelsep=period,justification=justified,
            singlelinecheck=false,skip=4pt]{caption}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage[hidelinks,breaklinks=true,pdftitle={The Great Rewiring},
            pdfauthor={William E. Shields}]{hyperref}
\urlstyle{same}

\pagestyle{fancy}\fancyhf{}
\fancyhead[C]{\footnotesize\scshape The Great Rewiring $\cdot$ Forecasting the Future 2026}
\fancyfoot[C]{\small\thepage}
\renewcommand{\headrulewidth}{0pt}
\fancypagestyle{plain}{\fancyhf{}\fancyfoot[C]{\small\thepage}\renewcommand{\headrulewidth}{0pt}}

\titlespacing*{\section}{0pt}{5pt plus 2pt minus 1pt}{4pt}
\titlespacing*{\subsection}{0pt}{8pt plus 2pt minus 2pt}{2.5pt}
\titleformat{\section}{\normalfont\large\bfseries}{\thesection}{0.6em}{}
\titleformat{\subsection}{\normalfont\normalsize\bfseries}{\thesubsection}{0.6em}{}

% leading is the page-count dial, and it is linear at ~0.13 page per 0.015
\linespread{@@L@@}
\setlength{\parskip}{0pt plus 0.6pt}
\setlength{\parindent}{1.2em}
\setlength{\emergencystretch}{2.2em}
\setlength{\columnsep}{16pt}
\setlength{\abovedisplayskip}{6pt}
\setlength{\belowdisplayskip}{6pt}
\renewcommand{\arraystretch}{1.06}
\setlength{\tabcolsep}{5pt}

% keep the four wide exhibits welded to the text that cites them
\setlength{\floatsep}{9pt plus 3pt minus 2pt}
\setlength{\textfloatsep}{11pt plus 3pt minus 3pt}
\setlength{\intextsep}{9pt plus 3pt minus 2pt}
\renewcommand{\topfraction}{0.92}\renewcommand{\bottomfraction}{0.80}
\renewcommand{\textfraction}{0.06}\renewcommand{\floatpagefraction}{0.85}
\setcounter{topnumber}{2}\setcounter{bottomnumber}{1}\setcounter{totalnumber}{3}

\hyphenpenalty=180 \tolerance=1200 \pretolerance=200
\widowpenalty=10000 \clubpenalty=10000 \brokenpenalty=9999
""".replace("@@PT@@", PT)
    .replace("@@M@@", MARG)
    .replace("@@L@@", LEAD)
    .replace("@@VT@@", VMAR.split(",")[0])
    .replace("@@VB@@", VMAR.split(",")[1])
)

DOC = r"""@@PRE@@
\begin{document}
\thispagestyle{plain}
\begin{center}
{\LARGE\bfseries The Great Rewiring}\\[6pt]
{\large Two Resource Grabs, One Network: Pricing Modern Mercantilism and AI\\ on the World Trade Web}\\[8pt]
{\scshape William E. Shields}\\[3pt]
August 1, 2026
\end{center}
\vspace{4pt}
\begin{center}\textbf{Abstract}\end{center}
\begin{adjustwidth}{}{}
\end{adjustwidth}
{\leftskip=2.2em \rightskip=2.2em \small
@@ABS@@
\par}
\vspace{4pt}
{\centering\small\textbf{Replication:} @@REPL@@\par}
\vspace{6pt}
{\footnotesize\textbf{Declaration of AI use.} @@DECL@@\par}
\vspace{8pt}
@@BODY@@
\end{document}
"""
for k, v in (
    ("@@PRE@@", PRE),
    ("@@ABS@@", abstract_tex),
    ("@@REPL@@", repl_tex),
    ("@@DECL@@", decl_tex),
    ("@@BODY@@", body),
):
    DOC = DOC.replace(k, v)

DOC = DOC.replace("\\begin{adjustwidth}{}{}\n\\end{adjustwidth}\n", "")
(BUILD / "paper.tex").write_text(DOC)

r = subprocess.run(
    ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", "-f", "paper.tex"],
    cwd=BUILD,
    capture_output=True,
    text=True,
)
pdf = BUILD / "paper.pdf"
if pdf.exists():
    import fitz

    n = len(fitz.open(str(pdf)))
    print(f"COMPILED  {PT}pt -> {n} pages")
    log = (BUILD / "paper.log").read_text(errors="ignore")
    print("overfull hboxes:", log.count("Overfull \\hbox"))
    print("undefined refs :", log.count("undefined"))
else:
    print("FAILED")
    print(r.stdout[-3000:])
