# FINDINGS

Eight numbered results, each stated with the conditions under which it holds. A finding quoted
without its conditions is a different claim from the one made here.

---

## F1. The Ported Generator Reproduces Its Published Statistics Within Approximately 3.5%

**Result.** Run across 1996 to 2020 under the published log-normal GDP conditions, the Python port
of the CompleNet 2022 world-trade-web generator reproduces six headline graph statistics within
approximately 3.5% of the published yearly averages. Those statistics are edge count, density, mean degree, mean
shortest-path length, mean clustering coefficient, and maximum k-core.

**Conditions.** The result holds only under the conditions it was measured in. Thirty independent
iterations averaged from seed base 42, the paper's own bootstrapped log-normal GDP conditions, and
the paper's density convention of edge count over n times n minus one. Table 2 was itself generated
under those GDP conditions, so validating against it requires them; this is the script's default
mode. The pass contract was set in advance at approximately 5% on the first five statistics and plus
or minus 10 on k-core.

**What the real-GDP path shows.** `--mode real` drives the same port with actual World Bank GDPs.
It is a diagnostic rather than the validation, it does not clear the Table 2 contract, and it is not
expected to: comparing real-GDP output against synthetically generated targets changes the driving
series and the target together.

**What it licenses.** The null in F4 can be attributed to the world rather than to the
implementation. **What it does not license.** Agreement on unweighted topology is not agreement on
weights, and the weight law is tested separately in `analysis/70_rf_rigor.py`.

**Source.** `models/validate_completnet.py`, `data/processed/port_validation.csv`.

---

## F2. Export Concentration in the Strategic Layers Is Severe and Uneven Across Sectors

**Result.** Across five strategic-sector layers built from BACI 2024 HS6 flows, the top three
exporters hold between approximately 38.4% and approximately 60.5% of layer exports. Batteries is
the most concentrated at approximately 50.0% for China alone and an export Herfindahl-Hirschman
index of approximately 2,657. Critical minerals is the least concentrated on this measure, at
approximately 23.4% for China and an index of approximately 913. Semiconductors sits
between the two, with Taiwan at approximately 19.6%, China at approximately 19.4%, and the top three
at approximately 51.7%.

**Conditions.** Export-origin shares within each layer for calendar 2024 only, computed on directed
flows in thousands of current US dollars after omitting edges below 1 kUSD. Layer membership is
defined by HS6 code prefix, so a product's assignment is a classification judgment rather than a
measured fact.

**What it does not license.** Export share is not control. A country with a modest export
share may sit on the shortest path between the large ones. The same table therefore reports weighted
betweenness alongside share, and the United States ranks first in critical-minerals betweenness
while holding approximately 6.0% of that layer's exports.

**Source.** `data/processed/multigraph/chokepoint_table.csv`,
`data/processed/multigraph/focus_country_ranks.csv`.

---

## F3. Strength-Targeted Removal Strands Roughly Ten Times More Trade Value Than Random Failure

**Result.** Removing the strongest 10% of nodes from the actual 2024 weighted network leaves
approximately 8.4% of original trade weight inside the surviving connected component.
Random failure of the same magnitude leaves approximately 83.7%. That is a roughly tenfold gap between an
adversary that chooses its targets and an accident that does not.

**Conditions.** Undirected weighted graph of all-products 2024 pair totals, node removal in
descending strength order, random band computed across 100 replicates from seed base 7000, and the
metric defined as surviving largest-connected-component weight as a share of **original** total
weight rather than of surviving weight.

**What it does not license.** Node removal is an abstraction and the curves bound damage rather than
forecast it. A state does not delete a country from the network, it re-prices a subset of
that country's edges. Percolating on edge subsets rather than whole nodes extends
this research.

**Source.** `analysis/41_attack.py`, `data/processed/attack_curves.csv`.

---

## F4. The Raw Counterfactual Reading, Recorded Here Only So Its Correction Can Be Followed

**Result.** A 300-member no-rewiring ensemble initialized on the actual 2020 network and evolved to
2028 places the China-US corridor near the 12th percentile of its own bands, with the Vietnam
connectors near the top.

**Conditions.** This finding is **superseded by F6 and must not be quoted on its own.** It fails the
test in F5. It is retained because a reader following the correction needs to see what was
corrected.

**Source.** `analysis/40_counterfactual.py`, `data/processed/counterfactual_corridors.csv`.

---

## F5. The Ensemble's Percentile Bands Are Not a Calibrated Null

**Result.** Across roughly 2,653 comparable country pairs in the 2020 to 2024 window, actual weights land
below the ensemble's 5th percentile approximately 28.3% of the time and above its 95th approximately
27.5% of the time, against 5% expected at each tail. The Kolmogorov-Smirnov distance to
U[0,1] is approximately 0.239. The generator's median within-pair dispersion is approximately 0.104
dex, where one dex is a factor of ten, against a real cross-sectional dispersion of
approximately 0.421 dex, so the bands run
approximately 4.1x too tight. A 2017 to 2019 pre-period backtest across roughly 2,928 country pairs
is worse, at a KS distance of approximately 0.305 and over-dispersion of approximately 10.7x.

**Conditions.** Percentiles computed against the same 300-member ensemble the paper prints, seeded
at 1000 for the main window and 5000 for the pre-period. Comparability requires a country pair to be
present and positive in both the actual panel and every ensemble draw.

**Why it is structural rather than a bug.** The generator's within-pair variation is Equation 8 GDP
jitter around an initialized weight. Real country pairs move for reasons the generator has no term for.
Therefore no seed, worker count, or ensemble size repairs that.

**Source.** `analysis/71_placebo.py`, `data/processed/placebo_results.json`.

---

## F6. Corrected Against an Empirical Null, Direction Survives and Magnitude Does Not

**Result.** Rebuilding the null from the cross-section of deviations, where r is the base-10 log of
actual weight over ensemble median weight, yields the following readings for the printed window.

| Corridor | Ratio vs benchmark median | Empirical percentile of all country pairs |
|---|---|---|
| CHN-USA | approximately 0.86x | approximately 34.4 |
| MEX-USA | approximately 0.94x | approximately 43.2 |
| CHN-VNM | approximately 1.25x | approximately 74.5 |
| VNM-USA | approximately 1.26x | approximately 74.8 |

*Source: Author (2026), `analysis/72_empirical_null.py`.*

China-US is suppressed relative to its GDP-implied benchmark and the connectors are elevated.
Both readings are ordinary-large rather than extreme.

**Conditions.** Percentiles are ranks among approximately 2,653 comparable country pairs, not
probabilities. The reference distribution contains the treated corridors, so the construction is
conservative by design.

**What it does not license.** The empirical null cannot distinguish a targeted shock from
an ordinary large one, so it reports direction and rank rather than significance. A pair-level
volatility model would restore a calibrated per-corridor null without discarding the generator, and
that is a natural extension of this research.

**Source.** `analysis/72_empirical_null.py`, `data/processed/empirical_null.json`.

---

## F7. Most of the China-US Suppression Predates the Ensemble's Start Line

**Result.** The same empirical-null construction applied to the 2017 to 2019 pre-period places the
China-US corridor at roughly the 21.8th percentile of all country pairs in 2019, against roughly the 34.4th
in 2024.

**Conditions.** Two separate ensembles on different initializations, so the comparison is between
two rankings rather than between two points on one scale.

**What it means.** Initializing on 2020 bakes the 2018 to 2019 trade-war suppression
into the initial condition. The ensemble therefore measures **incremental** rewiring since 2020
rather than cumulative rewiring since the first tariffs, and any reader comparing the two must hold
that distinction. This is also the cleanest available explanation for why the
descriptive gravity fit reports approximately 0.35x where the generator benchmark reports
approximately 0.86x. The gravity figure is the total displacement from a 2017 anchor; the generator
figure is the increment since 2020. Quote them in that order.

**Source.** `analysis/72_empirical_null.py`, `notes/PLACEBO-FINDING-2026-07-31.md`.

---

## F8. The Slate Is Ten Forecasts, Weighted Below Even, Scoring 0.150 at the Mode

**Result.** Ten binary forecasts, locked at v5.0 with stable IDs A1 through D10. Three sit at or
above 55, seven sit below even, the mean probability is 46.2, and the range is 20 to 75. The
modal-outcome Brier score is 0.150, approximately 40.0% better than a coin flip at 0.250.

**Conditions.** The modal-outcome score assumes every forecast resolves in the direction the
probability leans, which is a self-assessment rather than a result. The honest version of the same
number is the score recomputed against actual resolutions once they land.

**Provenance.** All ten probabilities were set by the author in a verification pass held separate
from model construction, and at least one was set against the model's own posterior on stated
judgment. Guardrail G3 in `AGENTS.md` governs any change to a printed probability, and the
largest such overlay, B5 at 20 against a model draft of 12, carries its dated rationale in
`notes/B5-OVERLAY-2026-08-01.md`.

**Source.** `notes/LOCKED-SLATE-v5.md`.

---

## Reading These Together

F1 through F8 price two grabs on one network and say how confident the pricing is. The honest summary is this. The topology results in F2 and F3 rest on
observed 2024 flows and are as strong as BACI itself, and the generator result in F1 is a clean
pass. The divergence results in F4 through F7 are directionally sound but weaker in
magnitude than the first draft of this work claimed. The instrument that produced that overclaim was
tested, found over-confident by approximately 4.1x, and replaced with one that survives its own
placebo. Building the pair-level volatility model that would recover the lost power is the most
valuable single extension available to this research.
