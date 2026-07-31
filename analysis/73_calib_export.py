#!/usr/bin/env python3
"""Our third research objective seeks to establish whether the no-rewiring ensemble constitutes
a calibrated null, and our fifth seeks to expose every instrument for inspection. To achieve
both at once we export the calibration histograms here so a reader can watch the placebo fail
in the interactive companion rather than take our word for it.

We re-run the printed 2020->2024 ensemble on the same seeds as 71 and 72, so the numbers
match the paper exactly, then dump for the demo:
  - a 20-bin histogram of raw ensemble percentiles, the flat-if-calibrated test
  - a histogram of deviations r = log10(actual / ensemble median), the empirical null
  - a summary of the within-dyad model sd distribution
  - named corridor markers on both scales
We add no new inference here. The math is identical to 71_placebo.py and 72_empirical_null.py.
"""
from __future__ import annotations
import json, sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, pandas as pd
from scipy import stats as sps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "models"))
from wtw_model import WTWModel  # noqa: E402

N_RUNS = 300
SEED_A = 1000
NAMED = [("CHN","USA"),("VNM","USA"),("MEX","USA"),("CHN","VNM"),("CHN","MEX"),("THA","USA")]
_G = {}

def load():
    wtw = pd.read_csv(ROOT/"data/processed/wtw_agg_2017_2024.csv", comment="#")
    wdi = pd.read_csv(ROOT/"data/processed/wdi_gdp_1995_2024.csv", comment="#")
    wdi = wdi.rename(columns={"country_iso3":"iso3","gdp_usd":"gdp"})
    gw = wdi.pivot_table(index="iso3", columns="year", values="gdp")
    ok = gw[list(range(2016,2025))].dropna().index
    traders = set(wtw.exporter_iso3) | set(wtw.importer_iso3)
    iso = sorted(set(ok) & traders); idx = {c:k for k,c in enumerate(iso)}; n=len(iso)
    def und(year):
        d = wtw[wtw.year==year]; A=np.zeros((n,n))
        ii,jj = d.exporter_iso3.map(idx), d.importer_iso3.map(idx)
        keep = ii.notna() & jj.notna()
        np.add.at(A,(ii[keep].astype(int),jj[keep].astype(int)), d.value_kusd[keep].to_numpy()*1e3)
        return A+A.T
    return iso, gw.loc[iso], {y:und(y) for y in range(2017,2025)}

def kappa_for(A,w):
    iu=np.triu_indices_from(A,1); e=A[iu]; m=e>0
    wmin=np.minimum.outer(w,w)[iu][m]
    return 10.0**(-(np.median(-np.log10(e[m]/wmin)) - sps.gamma.median(6.5571, scale=0.57943)))

def _init(A0,W): _G["A0"],_G["W"]=A0,W
def _run(seed):
    m=WTWModel(seed=seed); A,W=_G["A0"].copy(),_G["W"]
    for t in range(1,W.shape[1]): A=m.step(A,W[:,t],W[:,t-1])
    return A

if __name__=="__main__":
    iso,G,A_act = load()
    y0,y1 = 2020,2024
    w0=G[y0].to_numpy(); kap=kappa_for(A_act[y0],w0)
    A0=A_act[y0]*kap; W=G[list(range(y0,y1+1))].to_numpy()
    with ProcessPoolExecutor(max_workers=8, initializer=_init, initargs=(A0,W)) as ex:
        runs=list(ex.map(_run, range(SEED_A,SEED_A+N_RUNS), chunksize=10))
    n=len(iso); iu=np.triu_indices(n,1)
    cf=np.stack([r[iu] for r in runs]); act=(A_act[y1]*kap)[iu]
    live=(act>0)&(cf>0).all(axis=0)
    pct=(cf[:,live]<act[live]).mean(axis=0)
    lcf=np.log10(cf[:,live]); lact=np.log10(act[live])
    med=np.median(lcf,axis=0); r=lact-med; sdm=lcf.std(axis=0)
    pi,pj=iu[0][live],iu[1][live]
    pos={tuple(sorted((iso[pi[k]],iso[pj[k]]))):k for k in range(len(pi))}

    ph,pe = np.histogram(pct, bins=20, range=(0,1))
    lo,hi = -1.25, 1.25
    rh,re_ = np.histogram(np.clip(r,lo,hi), bins=40, range=(lo,hi))
    named={}
    for a,b in NAMED:
        k=pos.get(tuple(sorted((a,b))))
        if k is None: continue
        named[f"{a}-{b}"]={"raw_pct":float(pct[k]),"r":float(r[k]),
                           "ratio":float(10**r[k]),
                           "emp_pct":float((r<r[k]).mean()),
                           "sd_model":float(sdm[k])}
    out={"n":int(live.sum()),
         "pct_hist":{"counts":ph.tolist(),"edges":pe.round(4).tolist(),
                     "expected":float(live.sum()/20)},
         "r_hist":{"counts":rh.tolist(),"edges":re_.round(4).tolist()},
         "sd_cross":float(r.std()),"sd_model_med":float(np.median(sdm)),
         "over":float(r.std()/np.median(sdm)),
         "ks":float(sps.kstest(pct,"uniform").statistic),
         "below_p5":float((pct<0.05).mean()),"above_p95":float((pct>0.95).mean()),
         "named":named}
    json.dump(out, open(ROOT/"data/processed/calib_export.json","w"), indent=1)
    print("n",out["n"],"over",round(out["over"],2),"ks",round(out["ks"],3))
    for k,v in named.items(): print(" ",k,round(v["raw_pct"],3),round(v["ratio"],3),round(v["emp_pct"],3))
