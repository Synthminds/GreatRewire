# Interactive Companion: Build and Deploy

Our fifth research objective seeks to expose every instrument behind the paper to inspection
rather than to assertion. To achieve this objective we ship an interactive companion that reads
the same processed files the analysis reads, so a reader can watch the placebo fail and re-derive
the printed corridor readings in a browser instead of taking our word for either.

Live page: **https://neural-graph.vercel.app**
Data payload: **https://project-daw86.vercel.app/data.js** (plain JSON, CORS-open)

## Files

| File | Role |
|---|---|
| `index.template.html` | Authoring source, un-minified. The token `{{DATAURL}}` is substituted at build time. This is the file to edit. |
| `build_data.py` | Assembles `data.js` from `data/processed/*` plus the slate metadata block. Probabilities are transcribed from the printed forecast table and current values from the verified evidence notes, each carrying its own source label and as-of date. |
| `data.js` | `window.GR_DATA = {slate, x1, attack, g, cor, calib, enull}`. Serves as both the build output and a required build input. |

*Source: Author (2026).*

Of note, `build_data.py` reads the existing `data.js` before it writes one. Four blocks, namely
`x1`, `attack`, `g`, and `cor`, are carried forward from the previous bundle rather than recomputed,
because their producers are the exhibit scripts this repository does not ship. The two calibration
blocks, conversely, are rebuilt from `calib_export.json` and `empirical_null.json` on every run.
Deleting `data.js` therefore breaks the build rather than triggering a clean one, which is a real
fragility and an obvious candidate for future refinement.

## Rebuild

```bash
python3 analysis/73_calib_export.py                      # only if the calibration run changed
python3 demo/build_data.py                               # -> demo/data.js
sed -e 's|{{DATAURL}}|data.js|' demo/index.template.html > demo/index.html
python3 -m http.server -d demo 8000                      # open http://127.0.0.1:8000
```

Rebuilding against unchanged inputs reproduces `data.js` byte for byte. A non-empty diff therefore
means an input moved.

## Panels and What Each One Computes From

The Slate panel reads the ten printed probabilities. However, it draws a threshold gauge only where
a comparable published series exists. Where none does, as with A1's method conflict and A3's binary
event, the card says so rather than inventing a number.

Score It computes a Brier score client-side from the printed probabilities against whatever
resolution the reader sets. Baselines are 50 percent applied to everything, which scores 0.250,
and always-NO.

Additionally, Chokepoints renders the strategic-sector multigraph. Node removal recomputes stranded
value and component structure live.

Attack Lab draws the precomputed curves from `data/processed/attack_curves.csv`, and the live
panel percolates the real top-40 subnetwork in-browser.

Calibration Lab reads `analysis/71_placebo.py` and `analysis/72_empirical_null.py` output as
exported by `analysis/73_calib_export.py`. It runs the same seeds the paper ran, so the displayed
numbers match the printed ones exactly.

Rewiring Residual reads the `analysis/40_counterfactual.py` corridors. However, its raw percentile
differs from the Calibration Lab reading by roughly one to two points, because it runs to 2028 and
therefore requires IMF WEO coverage that drops some countries.

## Deployment Note

Of note, the page and its data live in two separate Vercel projects. `index.html` pulls `data.js` by
absolute URL through a plain `<script>` tag, so no CORS dependency exists. Should the data project
ever be removed, redeploying the bundle anywhere public and updating the single `<script src>` in
`index.template.html` restores the page.
