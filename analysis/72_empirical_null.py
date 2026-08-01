#!/usr/bin/env python3
"""This script establishes whether the no-rewiring ensemble constitutes
a calibrated null, and 71_placebo.py established that it does not. To achieve the objective
anyway we rebuild the null here from the cross-section of deviations rather than from the
model's own bands.

71_placebo.py found the raw ensemble percentile is NOT a p-value. Approximately 28% of
ordinary dyads land below the 5th percentile, because the generator's within-dyad
dispersion, which is Eq.-8 GDP jitter around an initialized weight, runs far narrower
than real dyad-level volatility. The remedy is Efron's move.

For each comparable dyad we compute the deviation r = log10(actual / median_cf). We then
ask where a named corridor's r sits in the empirical distribution of r across all
comparable dyads. That statement is honest, reading "bottom X% of all dyads by deviation
from the GDP-implied benchmark," and it survives the over-tight bands.

We also report the over-dispersion factor: cross-sectional sd(r) against the
median within-dyad model sd. That single number quantifies exactly how
over-confident the raw percentile was.

Of note, the empirical null buys honesty at the cost of power. It cannot distinguish a
targeted shock from an ordinary large one, so we report direction and rank rather than
significance, and a dyad-level volatility model would be a logical extension.
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "analysis"))
sys.path.insert(0, str(ROOT / "models"))
from wtw_model import WTWModel  # noqa: E402

N_RUNS = 300
NAMED = [("CHN", "USA"), ("VNM", "USA"), ("MEX", "USA"), ("CHN", "VNM"),
         ("CHN", "MEX"), ("THA", "USA")]
_G = {}


def load():
    wtw = pd.read_csv(ROOT / "data/processed/wtw_agg_2017_2024.csv", comment="#")
    wdi = pd.read_csv(ROOT / "data/processed/wdi_gdp_1995_2024.csv", comment="#")
    wdi = wdi.rename(columns={"country_iso3": "iso3", "gdp_usd": "gdp"})
    gw = wdi.pivot_table(index="iso3", columns="year", values="gdp")
    ok = gw[list(range(2016, 2025))].dropna().index
    traders = set(wtw.exporter_iso3) | set(wtw.importer_iso3)
    iso = sorted(set(ok) & traders)
    idx = {c: k for k, c in enumerate(iso)}
    n = len(iso)

    def und(year):
        d = wtw[wtw.year == year]
        A = np.zeros((n, n))
        ii, jj = d.exporter_iso3.map(idx), d.importer_iso3.map(idx)
        keep = ii.notna() & jj.notna()
        np.add.at(A, (ii[keep].astype(int), jj[keep].astype(int)),
                  d.value_kusd[keep].to_numpy() * 1e3)
        return A + A.T

    return iso, gw.loc[iso], {y: und(y) for y in range(2017, 2025)}


def kappa_for(A, w):
    iu = np.triu_indices_from(A, 1)
    e = A[iu]; m = e > 0
    wmin = np.minimum.outer(w, w)[iu][m]
    return 10.0 ** (-(np.median(-np.log10(e[m] / wmin))
                      - sps.gamma.median(6.5571, scale=0.57943)))


def _init(A0, W): _G["A0"], _G["W"] = A0, W


def _run(seed):
    m = WTWModel(seed=seed)
    A, W = _G["A0"].copy(), _G["W"]
    for t in range(1, W.shape[1]):
        A = m.step(A, W[:, t], W[:, t - 1])
    return A


def analyze(iso, G, A_act, y0, y1, seed0, label):
    w0 = G[y0].to_numpy()
    kap = kappa_for(A_act[y0], w0)
    A0 = A_act[y0] * kap
    W = G[list(range(y0, y1 + 1))].to_numpy()
    with ProcessPoolExecutor(max_workers=8, initializer=_init,
                             initargs=(A0, W)) as ex:
        runs = list(ex.map(_run, range(seed0, seed0 + N_RUNS), chunksize=10))
    n = len(iso); iu = np.triu_indices(n, 1)
    cf = np.stack([r[iu] for r in runs])
    act = (A_act[y1] * kap)[iu]
    live = (act > 0) & (cf > 0).all(axis=0)
    lcf = np.log10(cf[:, live]); lact = np.log10(act[live])
    med = np.median(lcf, axis=0)
    r = lact - med                                   # the deviation, in dex
    sd_model = lcf.std(axis=0)                       # the within-dyad model sd
    over = float(r.std() / np.median(sd_model))      # the over-dispersion factor
    pi, pj = iu[0][live], iu[1][live]
    pos = {tuple(sorted((iso[pi[k]], iso[pj[k]]))): k for k in range(len(pi))}

    print(f"\n=== {label} ({y0}->{y1}) ===")
    print(f"comparable dyads {live.sum()} | cross-sectional sd(r) {r.std():.3f} dex "
          f"| median within-dyad model sd {np.median(sd_model):.3f} dex "
          f"| OVER-DISPERSION {over:.1f}x")
    out = {"label": label, "y0": y0, "y1": y1, "n": int(live.sum()),
           "sd_cross": float(r.std()), "sd_model": float(np.median(sd_model)),
           "over_dispersion": over, "named": {}}
    for a, b in NAMED:
        k = pos.get(tuple(sorted((a, b))))
        if k is None:
            continue
        emp = float((r < r[k]).mean())               # the empirical-null percentile
        ratio = float(10 ** r[k])
        out["named"][f"{a}-{b}"] = {"dev_dex": float(r[k]),
                                    "ratio_vs_median": ratio,
                                    "empirical_pctile": emp}
        print(f"  {a}-{b}: {ratio:.2f}x benchmark median | {r[k]:+.3f} dex | "
              f"empirical percentile {emp*100:.1f} of all dyads")
    return out


if __name__ == "__main__":
    iso, G, A_act = load()
    res = {"main_2020_2024": analyze(iso, G, A_act, 2020, 2024, 1000,
                                     "MAIN (printed window)"),
           "pre_2017_2019": analyze(iso, G, A_act, 2017, 2019, 5000,
                                    "PRE-PERIOD backtest")}
    json.dump(res, open(ROOT / "data/processed/empirical_null.json", "w"), indent=1)
    m, p = res["main_2020_2024"], res["pre_2017_2019"]
    print("\n=== DOSE-RESPONSE (CHN-USA) ===")
    for tag, d in (("2019", p), ("2024", m)):
        c = d["named"].get("CHN-USA", {})
        print(f"  {tag}: {c.get('ratio_vs_median', float('nan')):.2f}x | "
              f"empirical pctile {c.get('empirical_pctile', float('nan'))*100:.1f}")
    print(f"\nover-dispersion: main {m['over_dispersion']:.1f}x, "
          f"pre {p['over_dispersion']:.1f}x")
