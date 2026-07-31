#!/usr/bin/env python3
"""Our third research objective seeks to establish whether the no-rewiring ensemble constitutes
a calibrated null. To achieve this objective we push every untreated dyad through the same
300-run ensemble and test the resulting percentiles for uniformity.

The claim under test is that "actual corridor X sits at the 12th percentile of a
300-run no-rewiring ensemble" constitutes evidence of rewiring. That claim is only
sound if the ensemble is a CALIBRATED null, meaning ordinary untreated dyads land
uniformly inside it. We therefore run two tests:

TEST A (uniformity placebo, the printed 2020->2024 ensemble):
  For every dyad present in both the actual panel and the ensemble, we compute
  the percentile of the actual weight within the 300 counterfactual draws. Under a
  calibrated null those percentiles are approximately U[0,1] across untreated dyads.
  We report the KS distance to U[0,1], the share landing in the extreme tails, and
  where the NAMED corridors sit relative to that reference distribution.

TEST B (pre-period dose-response, 2017->2019):
  We re-initialize on the actual BACI 2017 network and evolve to 2019 on actual
  GDP. That window contains the FIRST trade war but neither COVID nor the 2022+
  controls regime. If the method is a thermometer rather than a hallucination,
  CHN-USA should read cool but not cold here relative to its 2023-24 reading, and
  the untreated bulk should stay uniform.

Of note, this test is designed to be able to fail, and it does. Where it fails,
72_empirical_null.py rebuilds the null from the cross-section rather than quietly
retaining the raw percentile.

Runtime is approximately 6-10 minutes for two 300-run ensembles across 8 workers.
Output: data/processed/placebo_results.json, plus the console report.
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
sys.path.insert(0, str(ROOT / "models"))
from wtw_model import WTWModel  # noqa: E402

N_RUNS = 300
SEED_A, SEED_B = 1000, 5000
NAMED = [("CHN", "USA"), ("VNM", "USA"), ("MEX", "USA"), ("CHN", "VNM")]
_G = {}


def load():
    wtw = pd.read_csv(ROOT / "data/processed/wtw_agg_2017_2024.csv", comment="#")
    wdi = pd.read_csv(ROOT / "data/processed/wdi_gdp_1995_2024.csv", comment="#")
    wdi = wdi.rename(columns={"country_iso3": "iso3", "gdp_usd": "gdp"})
    gw = wdi.pivot_table(index="iso3", columns="year", values="gdp")
    need = list(range(2016, 2025))
    ok = gw[need].dropna().index
    traders = set(wtw.exporter_iso3) | set(wtw.importer_iso3)
    iso = sorted(set(ok) & traders)
    idx = {c: k for k, c in enumerate(iso)}
    n = len(iso)

    def undirected(year):
        d = wtw[wtw.year == year]
        A = np.zeros((n, n))
        ii, jj = d.exporter_iso3.map(idx), d.importer_iso3.map(idx)
        keep = ii.notna() & jj.notna()
        np.add.at(A, (ii[keep].astype(int), jj[keep].astype(int)),
                  d.value_kusd[keep].to_numpy() * 1e3)
        return A + A.T

    A_act = {y: undirected(y) for y in range(2017, 2025)}
    return iso, idx, gw.loc[iso], A_act


def kappa_for(A, w):
    iu = np.triu_indices_from(A, 1)
    e = A[iu]
    m = e > 0
    wmin = np.minimum.outer(w, w)[iu][m]
    F = -np.log10(e[m] / wmin)
    return 10.0 ** (-(np.median(F) - sps.gamma.median(6.5571, scale=0.57943)))


def _init(A0, W):
    _G["A0"], _G["W"] = A0, W


def _run(seed):
    m = WTWModel(seed=seed)
    A, W = _G["A0"].copy(), _G["W"]
    out = {}
    for t in range(1, W.shape[1]):
        A = m.step(A, W[:, t], W[:, t - 1])
        out[t] = A.copy()
    return out


def ensemble(iso, idx, G, A_act, y0, y1, seed0, label):
    w0 = G[y0].to_numpy()
    kap = kappa_for(A_act[y0], w0)
    A0 = A_act[y0] * kap
    W = G[list(range(y0, y1 + 1))].to_numpy()
    print(f"\n=== {label}: init {y0} -> {y1} | kappa=10^{-np.log10(kap):.3f} "
          f"| {len(iso)} countries, {N_RUNS} runs ===")
    with ProcessPoolExecutor(max_workers=8, initializer=_init,
                             initargs=(A0, W)) as ex:
        runs = list(ex.map(_run, range(seed0, seed0 + N_RUNS), chunksize=10))
    t_last = W.shape[1] - 1
    n = len(iso)
    iu = np.triu_indices(n, 1)
    cf = np.stack([r[t_last][iu] for r in runs])          # shape (runs, pairs)
    act = (A_act[y1] * kap)[iu]                            # shape (pairs,)
    live = (act > 0) & (cf > 0).all(axis=0)                # the comparable pairs only
    pct = (cf[:, live] < act[live]).mean(axis=0)
    ks = sps.kstest(pct, "uniform")
    lo, hi = (pct < 0.05).mean(), (pct > 0.95).mean()
    print(f"comparable dyads: {live.sum()}")
    print(f"percentile distribution vs U[0,1]: KS={ks.statistic:.3f} "
          f"(p={ks.pvalue:.3g}) | mean={pct.mean():.3f} median={np.median(pct):.3f}")
    print(f"tails: {lo*100:.1f}% below p5, {hi*100:.1f}% above p95 "
          f"(5.0% / 5.0% expected)")
    pi, pj = iu
    pos = {(iso[pi[k]], iso[pj[k]]): k for k in range(len(pi))}
    named = {}
    idx_live = np.where(live)[0]
    rank = {k: v for v, k in enumerate(idx_live)}
    for a, b in NAMED:
        key = tuple(sorted((a, b)))
        k = pos.get(key)
        if k is None or k not in rank:
            continue
        p = float(pct[rank[k]])
        named[f"{a}-{b}"] = p
        print(f"  {a}-{b}: percentile {p:.3f}")
    return dict(label=label, y0=y0, y1=y1, n_dyads=int(live.sum()),
                ks=float(ks.statistic), ks_p=float(ks.pvalue),
                mean=float(pct.mean()), median=float(np.median(pct)),
                frac_below_p5=float(lo), frac_above_p95=float(hi),
                named=named)


if __name__ == "__main__":
    iso, idx, G, A_act = load()
    res = {}
    res["A_2020_2024"] = ensemble(iso, idx, G, A_act, 2020, 2024, SEED_A,
                                  "TEST A - printed ensemble (2020->2024)")
    res["B_2017_2019"] = ensemble(iso, idx, G, A_act, 2017, 2019, SEED_B,
                                  "TEST B - pre-COVID backtest (2017->2019)")
    out = ROOT / "data/processed/placebo_results.json"
    json.dump(res, open(out, "w"), indent=1)
    print(f"\nwrote {out}")
    a, b = res["A_2020_2024"], res["B_2017_2019"]
    print("\n=== VERDICT INPUTS ===")
    print(f"A: bulk KS {a['ks']:.3f}, tails {a['frac_below_p5']*100:.1f}/"
          f"{a['frac_above_p95']*100:.1f}, CHN-USA {a['named'].get('CHN-USA')}")
    print(f"B: bulk KS {b['ks']:.3f}, tails {b['frac_below_p5']*100:.1f}/"
          f"{b['frac_above_p95']*100:.1f}, CHN-USA {b['named'].get('CHN-USA')}")
