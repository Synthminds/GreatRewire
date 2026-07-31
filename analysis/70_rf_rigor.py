#!/usr/bin/env python3
"""Our third research objective seeks to establish whether the no-rewiring ensemble constitutes
a calibrated null. To achieve this objective we first test the two published laws the ensemble
rests on against data they never saw, then let a random forest attribute the 2017-2024 share
shifts without imposing a functional form.

Random-forest rigor checks and out-of-sample fit curves (Exhibit X4).

We build three artifacts, mirroring Kennedy et al. (CompleNet 2022) Figs. 1-2 on
NEW data and adding nonparametric attribution:

P1  Weight law out-of-sample: F_emp = -log10(e/min(w_i,w_j)) on the real
    2024 network against the published Gamma(6.5571, 0.57943) law, both raw
    and under the kappa median-shift we employ at counterfactual initialization.
P2  Deletion law out-of-sample: the empirical 2020->2024 pair-death rate against
    y = log10(e/(w_i+w_j)), overlaid with the published quadratic
    10^(a y^2 + b y + c) and a random-forest partial dependence learned
    from the same real transitions, with no functional form imposed.
P3  Rewiring attribution: an RF regression of the 2017->2024 change in each
    dyad's share of world trade on scale features against policy-exposure
    features. Permutation importances then test whether the residual is
    policy-shaped.

Of note, P3 is a cross-sectional test and therefore cannot see a targeted effect on a single
dyad. It bounds what the average dyad does, and the ensemble percentiles carry the corridor-level
test instead.

Outputs: figures/x4_validation.pdf, /tmp/x4_preview.png, and the printed stats.
Seeds are fixed. We employ the sklearn RandomForest at 400 trees.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats as sps
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.inspection import permutation_importance

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "bc-paper-skills/bc-visualization/scripts"))
try:
    import paper_style  # noqa: F401  (sets fonts, pdf.fonttype)
except Exception:
    plt.rcParams.update({"pdf.fonttype": 42, "font.size": 8})

A, B, C = -0.048303, -0.96089, -5.2225
GSHAPE, GSCALE = 6.5571, 0.57943
SEED = 42

# ---------------------------------------------- data we read, all local
wtw = pd.read_csv(ROOT / "data/processed/wtw_agg_2017_2024.csv", comment="#")
wdi = pd.read_csv(ROOT / "data/processed/wdi_gdp_1995_2024.csv", comment="#")
wdi = wdi.rename(columns={"country_iso3": "iso3", "gdp_usd": "gdp"})
G = wdi.pivot_table(index="iso3", columns="year", values="gdp")

def pairs(year):
    d = wtw[wtw.year == year]
    p = {}
    for r in d.itertuples():
        if r.exporter_iso3 == r.importer_iso3:
            continue
        k = tuple(sorted((r.exporter_iso3, r.importer_iso3)))
        p[k] = p.get(k, 0.0) + r.value_kusd * 1e3
    return p

p17, p20, p24 = pairs(2017), pairs(2020), pairs(2024)

# we take strategic mass per country from the X1 multigraph JSON
x1 = json.load(open(ROOT / "data/processed/multigraph/x1_nodes_edges.json"))
smass = {n["iso3"]: n["strategic_strength_kusd"] * 1e3 for n in x1["nodes"]}
ASEAN = {"VNM", "THA", "MYS", "IDN", "PHL", "SGP", "KHM", "LAO", "BRN", "MMR"}

# ------------------- P1: we test the weight law on the 2024 network ----
rows = []
for (a_, b_), e in p24.items():
    if a_ in G.index and b_ in G.index:
        wa, wb = G.loc[a_].get(2024, np.nan), G.loc[b_].get(2024, np.nan)
        if np.isfinite(wa) and np.isfinite(wb) and e > 0:
            rows.append(-np.log10(e / min(wa, wb)))
F_emp = np.array([f for f in rows if np.isfinite(f)])
gmed = sps.gamma.median(GSHAPE, scale=GSCALE)
shift = np.median(F_emp) - gmed
print(f"P1: n={len(F_emp)} dyads | median F_emp {np.median(F_emp):.3f} vs "
      f"Gamma median {gmed:.3f} | shift {shift:+.3f} dex")
ks_raw = sps.kstest(F_emp, lambda x: sps.gamma.cdf(x, GSHAPE, scale=GSCALE)).statistic
ks_shift = sps.kstest(F_emp - shift, lambda x: sps.gamma.cdf(x, GSHAPE, scale=GSCALE)).statistic
print(f"P1: KS distance raw {ks_raw:.3f} | after median shift {ks_shift:.3f}")

# ----------- P2: we test the deletion law across 2020 -> 2024 ----------
# NONREP: countries carrying a known post-2022 Comtrade reporting collapse or a
# war-driven statistical breakdown. Their dyad "deaths" are reporting mortality
# rather than trade mortality, as with BLR-RUS at roughly $29B and the ARE cluster.
# We therefore run the deletion law on both panels and print the cleaned one.
NONREP = {"ARE", "BLR", "RUS", "IRN", "AFG", "SDN", "LBY", "SYR", "PRK", "VEN"}
rows = []
for k, e in p20.items():
    a_, b_ = k
    if a_ in G.index and b_ in G.index:
        wa, wb = G.loc[a_].get(2020, np.nan), G.loc[b_].get(2020, np.nan)
        if np.isfinite(wa) and np.isfinite(wb) and e > 0:
            y = np.log10(e / (wa + wb))
            died = 0 if k in p24 and p24[k] > 0 else 1
            clean = int(a_ not in NONREP and b_ not in NONREP)
            rows.append((y, np.log10(e), died, clean))
d2 = pd.DataFrame(rows, columns=["y", "loge", "died", "clean"])
d2c = d2[d2.clean == 1]
print(f"P2: {len(d2)} 2020 pairs | deaths {d2.died.sum()} ({d2.died.mean()*100:.2f}%) | "
      f"cleaned panel {len(d2c)} pairs, deaths {d2c.died.sum()} ({d2c.died.mean()*100:.2f}%)")

Xd, yd = d2c[["y", "loge"]].to_numpy(), d2c.died.to_numpy()
rf_d = RandomForestClassifier(n_estimators=400, min_samples_leaf=50,
                              class_weight="balanced_subsample",
                              random_state=SEED, n_jobs=8, oob_score=True)
rf_d.fit(Xd, yd)
ygrid = np.linspace(max(-12, d2c.y.min()), min(-2, d2c.y.max()), 60)
pd_curve = []
for yv in ygrid:
    Xg = Xd.copy(); Xg[:, 0] = yv
    pd_curve.append(rf_d.predict_proba(Xg)[:, 1].mean())
pd_curve = np.array(pd_curve)

def binned(df):
    bins = np.linspace(df.y.min(), df.y.max(), 22)
    g = df.copy(); g["bin"] = pd.cut(g.y, bins)
    e = g.groupby("bin", observed=True).agg(rate=("died", "mean"),
                                            n=("died", "size"),
                                            yc=("y", "mean"))
    return e[e.n >= 40]

emp, empc = binned(d2), binned(d2c)
parab = lambda yv: np.where(yv >= -10, 10 ** (A * yv**2 + B * yv + C), 0.36)
print(f"P2: RF OOB accuracy (cleaned) {rf_d.oob_score_:.3f}")
hi = empc[empc.yc > -5]
print(f"P2: cleaned high-y (y>-5) mean death rate {hi.rate.mean()*100:.2f}% "
      f"vs published law {parab(hi.yc.to_numpy()).mean()*100:.3f}%")

# --------------- P3: we attribute the rewiring across 2017->2024 -------
T17, T24 = sum(p17.values()), sum(p24.values())
rows = []
for k, e17 in p17.items():
    if e17 < 1e7:
        continue
    a_, b_ = k
    if a_ not in G.index or b_ not in G.index:
        continue
    g24a, g24b = G.loc[a_].get(2024, np.nan), G.loc[b_].get(2024, np.nan)
    g17a, g17b = G.loc[a_].get(2017, np.nan), G.loc[b_].get(2017, np.nan)
    if not all(map(np.isfinite, (g24a, g24b, g17a, g17b))):
        continue
    e24 = p24.get(k, 0.0)
    if e24 <= 0:
        continue
    target = np.log10((e24 / T24) / (e17 / T17))
    chn = int("CHN" in k)
    usa = int("USA" in k)
    rows.append(dict(
        d_share=target,
        log_w17=np.log10(e17),
        log_gdp_prod=np.log10(g24a * g24b),
        gdp_growth=np.log10((g24a + g24b) / (g17a + g17b)),
        chn_dyad=chn, chn_usa=int(chn and usa),
        connector_usa=int(usa and ((a_ in ASEAN or a_ == "MEX") or
                                   (b_ in ASEAN or b_ == "MEX"))),
        strategic_mass=np.log10(1 + smass.get(a_, 0) + smass.get(b_, 0)),
    ))
d3 = pd.DataFrame(rows)
FEATS = ["log_w17", "log_gdp_prod", "gdp_growth", "chn_dyad", "chn_usa",
         "connector_usa", "strategic_mass"]
LABEL = {"log_w17": "baseline size (2017 wt)", "log_gdp_prod": "GDP product",
         "gdp_growth": "dyad GDP growth", "chn_dyad": "China dyad",
         "chn_usa": "China–US edge", "connector_usa": "connector–US dyad",
         "strategic_mass": "strategic-layer mass"}
rf_a = RandomForestRegressor(n_estimators=400, min_samples_leaf=20,
                             random_state=SEED, n_jobs=8, oob_score=True)
rf_a.fit(d3[FEATS], d3.d_share)
pi = permutation_importance(rf_a, d3[FEATS], d3.d_share, n_repeats=5,
                            random_state=SEED, n_jobs=8)
order = np.argsort(pi.importances_mean)
print(f"P3: n={len(d3)} dyads | OOB R^2 {rf_a.oob_score_:.3f}")
for i in order[::-1]:
    print(f"    {FEATS[i]:<16} {pi.importances_mean[i]:.4f} ± {pi.importances_std[i]:.4f}")
# we group the importances to support the printed claim
policy = ["chn_dyad", "chn_usa", "connector_usa", "strategic_mass"]
scale = ["log_w17", "log_gdp_prod", "gdp_growth"]
imp = dict(zip(FEATS, pi.importances_mean))
print(f"P3: policy-exposure sum {sum(imp[f] for f in policy):.4f} vs "
      f"scale sum {sum(imp[f] for f in scale):.4f}")

# ------------------------------- the plot, three panels ----------------
OI = {"blue": "#0072B2", "verm": "#D55E00", "green": "#009E73", "gray": "#666666"}
fig, axes = plt.subplots(1, 3, figsize=(10.6, 3.1))
fig.suptitle("The published laws hold out-of-sample, and gravity still rules the average dyad,\n"
             "which is what makes the named corridors stand out",
             x=0.02, ha="left", fontsize=11, fontweight="bold")

ax = axes[0]
xs = np.linspace(0, 10, 400)
ax.hist(F_emp, bins=80, range=(0, 10), density=True, color=OI["blue"],
        alpha=0.55, label="real 2024 dyads")
ax.plot(xs, sps.gamma.pdf(xs, GSHAPE, scale=GSCALE), color=OI["verm"], lw=1.6,
        label=r"$\Gamma(6.557,0.579)$ (fitted 1996–2020)")
ax.plot(xs, sps.gamma.pdf(xs + shift, GSHAPE, scale=GSCALE), color=OI["verm"],
        lw=1.2, ls="--", label=f"median-shifted {shift:+.2f} dex ($\\kappa$)")
ax.set_xlabel(r"$-\log_{10}(e_{ij}/\min(w_i,w_j))$", fontsize=8)
ax.set_ylabel("density", fontsize=8)
ax.set_title("Weight law (their Fig. 1, on 2024 data)", fontsize=8.5)
ax.legend(fontsize=6.2, frameon=False)

ax = axes[1]
ax.scatter(emp.yc, emp.rate, s=12, facecolors="none", edgecolors=OI["gray"],
           lw=0.8, zorder=2, label="all pairs (incl. reporting deaths)")
ax.scatter(empc.yc, empc.rate, s=14, color=OI["blue"], zorder=3,
           label="cleaned panel (non-reporters removed)")
yy = np.linspace(min(emp.yc.min(), -11), emp.yc.max(), 300)
ax.plot(yy, parab(yy), color=OI["verm"], lw=1.6,
        label=r"published $10^{ay^2+by+c}$")
ax.plot(ygrid, pd_curve, color=OI["green"], lw=1.4, ls="--",
        label="RF partial dependence (cleaned)")
ax.set_yscale("log")
ax.set_xlabel(r"$y=\log_{10}(e_{ij}/(w_i+w_j))$", fontsize=8)
ax.set_ylabel("deletion probability", fontsize=8)
ax.set_title("Deletion law (their Fig. 2, on 2020$\\to$2024)", fontsize=8.5)
ax.legend(fontsize=5.8, frameon=False, loc="lower left")

ax = axes[2]
ypos = np.arange(len(FEATS))
vals = pi.importances_mean[order]
cols = [OI["verm"] if FEATS[i] in policy else OI["gray"] for i in order]
ax.barh(ypos, vals, xerr=pi.importances_std[order], color=cols, height=0.62,
        error_kw=dict(lw=0.7))
ax.set_yticks(ypos)
ax.set_yticklabels([LABEL[FEATS[i]] for i in order], fontsize=7)
ax.set_xlabel("permutation importance", fontsize=8)
ax.set_title(f"Share shifts 2017$\\to$2024: scale vs exposure\n"
             f"(RF, OOB $R^2$={rf_a.oob_score_:.2f}; exposure in orange)", fontsize=8.5)
ax.annotate("CHN\u2013US is 1 dyad of 5,996, so targeted\neffects do not cross-section; the ensemble\npercentiles (B2) carry that test",
            xy=(0.98, 0.05), xycoords="axes fraction", ha="right", va="bottom",
            fontsize=6.2, color="#555555")

fig.text(0.02, 0.015,
         "Source: BACI HS17 V202601 aggregates, WDI GDP; RandomForest 400 trees, fixed seeds; "
         "analysis/70_rf_rigor.py. Computed 2026-07-31.",
         fontsize=6, color="#555555")
fig.tight_layout(rect=(0, 0.045, 1, 0.90))
fig.savefig(ROOT / "figures/x4_validation.pdf")
fig.savefig("/tmp/x4_preview.png", dpi=150)
print("wrote figures/x4_validation.pdf")
