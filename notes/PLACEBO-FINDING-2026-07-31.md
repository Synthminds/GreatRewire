# PLACEBO RESULT: The Null Is Over-Tight, and Two Benchmarks Are Fused in Print

Run: `analysis/71_placebo.py` for the calibration test and `analysis/72_empirical_null.py` for the
correction.

Status at the time of writing: **NOT IMPLEMENTED, awaiting ruling.** This was raised as a G1/G4
flag rather than made as a silent change. Status as shipped: the ruling went to Option A below,
and the paper prints the failed test alongside the corrected reading. This document is preserved
as the original finding rather than rewritten after the fact.

## Finding 1 (severity 5): The Ensemble Percentile Is Not a P-Value

Placebo test: for every comparable dyad, where does the actual 2024 weight sit inside the 300-run
no-rewiring ensemble? Under a calibrated null those percentiles are approximately uniform. They
are not.

| Window | Dyads | KS vs U[0,1] | Below p5 | Above p95 | Over-dispersion |
|---|---|---|---|---|---|
| 2020 to 2024 (printed) | 2,653 | 0.239 | **28.3%** (5% expected) | **27.5%** | **4.1x** |
| 2017 to 2019 (pre-period) | 2,928 | 0.305 | 34.7% | 30.8% | 10.7x |

*Source: Author (2026), `analysis/71_placebo.py`.*

The cause is structural rather than a port bug. The generator's within-dyad dispersion is Eq.-8
GDP jitter around an initialized weight, at a median model standard deviation of approximately
0.104 dex, while real dyads move approximately 0.421 dex cross-sectionally. The bands run roughly
4x too tight. **A raw percentile of 12 is therefore unremarkable when approximately 28% of all
dyads sit below 5.**

**Correction (Efron empirical null):** build the null from the cross-section of deviations
r = log10(actual / ensemble median) instead of from the model's own bands. The result for the
printed window follows.

| Corridor | Ratio vs ensemble median | Empirical percentile of all dyads |
|---|---|---|
| CHN-USA | 0.86x | **34.4** (bottom third) |
| MEX-USA | 0.94x | 43.2 |
| CHN-VNM | 1.25x | 74.5 |
| VNM-USA | 1.26x | **74.8** (top quarter) |

*Source: Author (2026), `analysis/72_empirical_null.py`.*

Direction survives, with China-US suppressed and the connectors elevated. However, the magnitudes
are ordinary-large rather than extreme.

## Finding 2 (severity 3): Section 4 and the Abstract Fuse Two Different Instruments

The printed sentence reads "China-US trades at 0.35x its GDP-implied weight, the 12th to 15th
percentile of the ensemble." Those are **two separate analyses**:

- **0.35x and 16.2x** come from the descriptive per-year gravity OLS on directed flows, refit
  each year (`analysis/21`; the actuals-metrics note says explicitly "NOT the published CompleNet
  model"). Legitimate, sourced, and unchanged.
- **The 12th to 15th percentile** comes from the CompleNet counterfactual on undirected pair
  weights, **initialized on the 2020 network**. Its own median ratio for CHN-USA is **0.86x**,
  not 0.35x.

Both are true, and they measure against different baselines. The gap has a clean explanation worth
printing: initializing on 2020 bakes the 2018 to 2019 trade-war suppression into the initial
condition, so the ensemble measures only **incremental** rewiring since 2020. The supporting
evidence is the pre-period backtest, which puts CHN-USA at the 21.8th empirical percentile in 2019
against 34.4th in 2024. Most of the suppression therefore predates the ensemble's start line.

Risk if unaddressed: the repository is available on request, and a judge who re-runs
`40_counterfactual.py` finds 0.86x where the paper says 0.35x in the same breath.

## Recommended Fix (Option A)

1. Separate the instruments in the abstract and section 4, naming the gravity benchmark and the
   generator benchmark as two readings that bracket the same direction.
2. Replace raw-percentile language with the empirical-null statement, reading "bottom third of all
   dyads by deviation from the GDP-implied benchmark".
3. Add three sentences to B3 disclosing the placebo, the 4.1x over-dispersion, and the correction,
   so the failure is self-caught and self-corrected in print.
4. Keep 0.35x and 16.2x exactly as they are, attributed to the gravity fit.

Net effect: the paper's weakest quantitative claim becomes its strongest methodological one, since
a forecaster who placebo-tests his own null, finds it over-confident, and prints the correction
has demonstrated the discipline the instrument itself failed to supply. The cost is approximately
0.25pp of page budget.

Slate impact: none. No forecast probability depends on the percentile figure.

---

*Correction, 2026-08-01: this note originally described the gravity OLS as "fitted
on 2017". It is refit on each year's cross-section; `data/processed/actuals_metrics.csv`
carries a separate fit per year, and the printed 0.35x and 16.2x are the 2024 residuals.
The finding this note records is unaffected.*
