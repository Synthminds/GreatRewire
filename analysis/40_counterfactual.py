#!/usr/bin/env python3
"""This script reads the present as deviations from a world that never
rewired. To achieve this objective we initialize the ensemble on the ACTUAL 2020 network and
evolve it forward across 2021-2028 under the validated CompleNet port on actual GDPs. The
divergence between that ensemble and the actual 2021-2024 networks is the rewiring, quantified.

Design (notes/completnet-spec.md, Forward-use):
- We initialize from BACI 2020 undirected aggregates, rescaled to model units
  (kappa: the median of -log10(e/min(w_i,w_j)) matched to the paper's
  Gamma(6.5571, 0.57943) median).
- We evolve with published parameters and GDP = WDI 2020-2024 spliced to IMF WEO
  (Apr-2026) 2025-2028, ratio-spliced at 2024 so no level jump enters the run.
- We take an N_RUNS ensemble and compute divergence against actual on the same
  kappa scale: corridor percentiles, connector-share gain, and L1 share
  divergence against a model-noise baseline.

Of note, the raw corridor percentiles printed here are NOT calibrated p-values. Our third
objective tests exactly that in 71_placebo.py and corrects it in 72_empirical_null.py; read
those before quoting a percentile from this file.

Output: data/processed/counterfactual_ensemble.csv (+ corridors file).
Runtime: approximately 2-4 minutes with the process pool.
"""
from __future__ import annotations

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
SEED0 = 1000
YEARS_CF = list(range(2021, 2029))
ASEAN10 = ["VNM", "THA", "MYS", "IDN", "PHL", "SGP", "KHM", "LAO", "BRN", "MMR"]
CORRIDORS = [("CHN", "USA"), ("CHN", "VNM"), ("CHN", "MEX"), ("CHN", "THA"),
             ("MEX", "USA"), ("VNM", "USA"), ("THA", "USA"), ("MYS", "USA"), ("IDN", "USA")]

_G = {}  # worker globals, populated once per process by _init_worker


def load_inputs():
    wtw = pd.read_csv(ROOT / "data/processed/wtw_agg_2017_2024.csv", comment="#")
    wdi = pd.read_csv(ROOT / "data/processed/wdi_gdp_1995_2024.csv", comment="#")
    weo = pd.read_csv(ROOT / "data/processed/imf_weo_ngdpd_2020_2028.csv", comment="#")

    wdi = wdi.rename(columns={"country_iso3": "iso3", "gdp_usd": "gdp"})
    weo = weo.rename(columns={"economy_code": "iso3", "ngdpd_bn_usd": "gdp_busd"})

    gw = wdi.pivot_table(index="iso3", columns="year", values="gdp")
    ge = weo.pivot_table(index="iso3", columns="year", values="gdp_busd") * 1e9

    need_wdi = list(range(2019, 2025))
    ok = gw[need_wdi].dropna().index
    ok = ok.intersection(ge[[2025, 2026, 2027, 2028]].dropna().index)

    # we ratio-splice WEO 2025-2028 onto WDI's 2024 level so no level jump enters the run
    G = {}
    for y in range(2020, 2025):
        G[y] = gw.loc[ok, y]
    scale = gw.loc[ok, 2024] / ge.loc[ok, 2024]
    for y in range(2025, 2029):
        G[y] = ge.loc[ok, y] * scale
    G = pd.DataFrame(G)

    # we build the actual undirected networks 2020-2024 over the common country set
    traders = set(wtw.exporter_iso3) | set(wtw.importer_iso3)
    iso = sorted(set(G.index) & traders)
    G = G.loc[iso]
    idx = {c: k for k, c in enumerate(iso)}
    n = len(iso)

    def undirected(year):
        d = wtw[wtw.year == year]
        A = np.zeros((n, n))
        ii = d.exporter_iso3.map(idx)
        jj = d.importer_iso3.map(idx)
        keep = ii.notna() & jj.notna()
        np.add.at(A, (ii[keep].astype(int), jj[keep].astype(int)), d.value_kusd[keep] * 1e3)
        return A + A.T  # symmetric, so the pair weight carries flows in both directions

    A_act = {y: undirected(y) for y in range(2020, 2025)}
    return iso, G, A_act


def kappa_rescale(A2020, w2020):
    """Match the median empirical F to the paper's Gamma median under the model-unit convention."""
    iu = np.triu_indices_from(A2020, 1)
    e = A2020[iu]
    m = e > 0
    wmin = np.minimum.outer(w2020, w2020)[iu][m]
    F_emp = -np.log10(e[m] / wmin)
    F_target = sps.gamma.median(6.5571, scale=0.57943)  # approximately 3.607
    log10_kappa = np.median(F_emp) - F_target
    return 10.0 ** (-log10_kappa), float(np.median(F_emp)), float(F_target)


def _init_worker(A0, Wmat):
    _G["A0"] = A0
    _G["W"] = Wmat


def _run_one(seed):
    model = WTWModel(seed=seed)
    A = _G["A0"].copy()
    W = _G["W"]  # nine columns, 2020..2028
    outs = {}
    for t in range(1, W.shape[1]):
        A = model.step(A, W[:, t], W[:, t - 1])
        outs[2020 + t] = A.copy()
    return outs


def summarize(iso, G, A_act):
    n = len(iso)
    idx = {c: k for k, c in enumerate(iso)}
    w2020 = G[2020].to_numpy()
    kappa, f_med, f_tgt = kappa_rescale(A_act[2020], w2020)
    A0 = A_act[2020] * kappa
    act = {y: A_act[y] * kappa for y in A_act}
    Wmat = G[[y for y in range(2020, 2029)]].to_numpy()
    print(f"countries: {n} | kappa=10^{-np.log10(kappa):.3f} inverse "
          f"(median F_emp {f_med:.3f} -> target {f_tgt:.3f})")

    with ProcessPoolExecutor(max_workers=8, initializer=_init_worker, initargs=(A0, Wmat)) as ex:
        runs = list(ex.map(_run_one, range(SEED0, SEED0 + N_RUNS), chunksize=10))
    print(f"ensemble: {len(runs)} runs complete")

    iu = np.triu_indices(n, 1)
    asean_ids = [idx[c] for c in ASEAN10 if c in idx]
    conn_ids = sorted(set(asean_ids + ([idx["MEX"]] if "MEX" in idx else [])))

    def corridor(A, a, b):
        return A[idx[a], idx[b]] if a in idx and b in idx else np.nan

    def conn_share(A):
        s = A.sum(axis=1)
        return s[conn_ids].sum() / s.sum()

    def shares(A):
        e = A[iu]
        return e / e.sum()

    rows, crows = [], []
    for y in YEARS_CF:
        cf_tot = np.array([r[y].sum() / 2 for r in runs])
        cf_conn = np.array([conn_share(r[y]) for r in runs])
        rows.append(("cf_total_weight", y, *np.percentile(cf_tot, [50, 5, 95])))
        rows.append(("cf_connector_share", y, *np.percentile(cf_conn, [50, 5, 95])))
        for a, b in CORRIDORS:
            cvals = np.array([corridor(r[y], a, b) for r in runs])
            crows.append((f"{a}-{b}", y, "cf", *np.percentile(cvals, [50, 5, 95])))
        if y in act:
            A_a = act[y]
            sh_a = shares(A_a)
            l1 = np.array([0.5 * np.abs(shares(r[y]) - sh_a).sum() for r in runs])
            base = np.array([0.5 * np.abs(shares(runs[k][y]) - shares(runs[k + 1][y])).sum()
                             for k in range(0, min(100, len(runs) - 1))])
            rows.append(("l1_divergence_actual", y, *np.percentile(l1, [50, 5, 95])))
            rows.append(("l1_model_noise", y, *np.percentile(base, [50, 5, 95])))
            rows.append(("actual_connector_share", y, conn_share(A_a), np.nan, np.nan))
            cf_conn_pct = float((cf_conn < conn_share(A_a)).mean())
            rows.append(("connector_share_pctile_of_actual_in_cf", y, cf_conn_pct, np.nan, np.nan))
            for a, b in CORRIDORS:
                av = corridor(A_a, a, b)
                cvals = np.array([corridor(r[y], a, b) for r in runs])
                crows.append((f"{a}-{b}", y, "actual", av, np.nan, np.nan))
                crows.append((f"{a}-{b}", y, "pctile_of_actual_in_cf",
                              float((cvals < av).mean()), np.nan, np.nan))

    hdr = ("# source: models/wtw_model.py ensemble (validated port), BACI 2020 init, "
           "WDI+WEO GDPs\n# built: 2026-07-30\n# script: analysis/40_counterfactual.py\n"
           f"# runs: {N_RUNS}, seeds {SEED0}+, kappa median-matched; weights in model units\n")
    df = pd.DataFrame(rows, columns=["metric", "year", "p50", "p5", "p95"])
    with open(ROOT / "data/processed/counterfactual_ensemble.csv", "w") as f:
        f.write(hdr); df.to_csv(f, index=False)
    dc = pd.DataFrame(crows, columns=["corridor", "year", "kind", "p50", "p5", "p95"])
    with open(ROOT / "data/processed/counterfactual_corridors.csv", "w") as f:
        f.write(hdr); dc.to_csv(f, index=False)

    # headline print: the excess over model noise, then the corridor percentiles
    print("\n=== HEADLINES ===")
    for y in range(2021, 2025):
        l1 = df[(df.metric == "l1_divergence_actual") & (df.year == y)].p50.iloc[0]
        nz = df[(df.metric == "l1_model_noise") & (df.year == y)].p50.iloc[0]
        print(f"{y}: L1 divergence {l1:.4f} vs model-noise {nz:.4f} (excess {l1/nz:.2f}x)")
    for cor in ["CHN-USA", "VNM-USA", "MEX-USA"]:
        p = dc[(dc.corridor == cor) & (dc.kind == "pctile_of_actual_in_cf")]
        print(f"{cor} percentile of actual within counterfactual ensemble: "
              + ", ".join(f"{int(r.year)}: {r.p50:.3f}" for r in p.itertuples()))


if __name__ == "__main__":
    iso, G, A_act = load_inputs()
    summarize(iso, G, A_act)
