# METHOD

How the generator works, how we employ it as a null, how that null failed its own test, and what we
did about it.

---

## A. The Generator

Our second research objective seeks to hold fixed the machine that explained the last twenty-five
years of the world trade web and to run it forward as a null for a world that never rewired. To
achieve this objective we port that machine to Python in `models/wtw_model.py`, reproducing
Equations 2 through 8 exactly as published. The source is Kennedy, Wish, Smith, Sherrell, Shields
and Gera, "Building a Reliable, Dynamic and Temporal Synthetic Model of the World Trade Web"
(CompleNet 2022), and reproducing it verbatim is what lets the null carry no discretion of ours.

The model represents the world trade web as an undirected weighted graph on national economies, and
it is driven by one exogenous input: a GDP vector per year. Equation 2 converts GDP to a fitness,
dividing each economy's GDP by the cross-sectional mean, so the model is scale-free in the units
supplied. Equations 3 and 5 set the probability that a pair is linked as a saturating function of
the product of the two fitnesses, using coefficients of 220 and 80 at initialization and 200 and 80
in growth years, clamped to the unit interval. Equation 4 draws the weight of a newly created edge
as ten raised to the negative of a Gamma variate, with shape approximately 6.5571 and scale
approximately 0.57943, multiplied by the smaller of the two GDPs. Equations 6 and 7 delete existing
edges with a probability that follows a quadratic in the base-10 log of the edge weight over the GDP
sum, floored at approximately 0.36 below a log ratio of negative ten. Finally, Equation 8 adjusts
surviving edges multiplicatively against the year-over-year change in the smaller economy, holding
weights inside a jitter band of roughly 0.95 to 1.05 when that change is small.

Two features of the port deserve naming because they are ours rather than the paper's. The first is
a floor of 0.05 on the Equation 8 adjustment factor, which the paper leaves undefined for
contractions steeper than 50%, and without which a severe contraction would drive an edge weight
negative. The second is that we route all randomness through a single NumPy `Generator` per model
instance, which makes an ensemble member a pure function of its seed. However, both choices are
documented at the point of use in `PARAMS` rather than buried, and neither touches the published
functional forms.

Weights live in what the code calls model units, on the Equation 4 scale. Of note, they are not
dollars, and comparing them to real trade values requires the rescaling described in section C.

---

## B. Validating the Port

Our objective here is narrower and it is a precondition for everything after it. Before we may call
the port the published model, it must reproduce the published model's own reported statistics on
data the published model was fitted to explain.

`models/validate_completnet.py` runs the port across 1996 to 2020 driven by real World Bank GDPs,
averaging 30 independent iterations from seed base 42, and compares yearly-average graph statistics
against the anchors transcribed from the paper's Tables 1 and 2. Of note, the compared statistics
are edge count, density, mean degree, mean shortest-path length, mean clustering coefficient, and
the maximum k-core, alongside their dispersions. The pass contract requires agreement within
approximately 5% on the first five and k-core within plus or minus 10.

The port passes, reproducing six headline statistics within approximately 3.5%. This translates to a
null whose disagreement with the real network can be attributed to the world rather than to the
implementation. Additionally, the script offers a `--mode bootstrap` path that regenerates the
paper's own log-normal GDP conditions rather than real GDPs, which isolates whether a deviation
comes from the model or from the driving series.

One caveat bounds the validation. The paper specifies its GDP bootstrap only as approximately
linear in log with a drift near 0.058 per year, so our bootstrap adopts a log-random-walk with
constant dispersion where the paper's dispersion drifts slightly. Tightening that law against the
published figure is a logical extension of this check, and it would not change the real-GDP result
reported above.

---

## C. The Counterfactual as a Null

Our objective in `analysis/40_counterfactual.py` is to read the present as deviations from a world
that never rewired. To achieve this objective we initialize the ensemble on the **actual** 2020
network rather than on a synthetic one, then evolve it forward across 2021 to 2028 under the
validated port on actual GDPs.

Three construction choices govern the result. First, the initialization rescales actual BACI 2020
undirected pair weights into model units through a constant we call kappa, fixed by matching the
median of the negative base-10 log of the weight over the smaller GDP to the median of the
published Gamma law. Second, GDP is World Bank WDI for 2020 through 2024 spliced to IMF WEO
April 2026 projections for 2025 through 2028, ratio-spliced at 2024 so no level jump enters the
run. Lastly, the ensemble is 300 members seeded from 1000, evaluated across eight worker processes,
with member results depending on rank rather than on scheduling order.

From this, the measurement is a comparison of the actual 2021 to 2024 network against the ensemble
on the same kappa scale, reported as corridor percentiles, connector-share gain, and an L1 share
divergence against a model-noise baseline. Initializing on 2020 has a consequence worth stating
plainly rather than discovering later: it bakes the 2018 to 2019 trade-war suppression into the
initial condition, so the ensemble measures **incremental** rewiring since 2020 rather than
cumulative rewiring since the first tariffs.

Moreover, two supporting methods sit alongside the ensemble. `analysis/41_attack.py` percolates the
actual 2024 weighted network under strength-targeted, betweenness-targeted, and random node removal
across 100 random-order replicates, reporting surviving connected weight as a share of original
weight. `analysis/70_rf_rigor.py` tests the two published laws on data they never saw, then lets a
random forest at 400 trees attribute the 2017 to 2024 share shifts without imposing a functional
form. Node removal in the percolation is an abstraction and we fence it accordingly: a state does
not delete a country from the network, it re-prices a subset of that country's edges, so the curves
bound the damage rather than forecast it.

---

## D. The Calibration Failure

Our third research objective seeks to establish whether the no-rewiring ensemble constitutes a
calibrated null. `analysis/71_placebo.py` implements the test, and the test is designed to be able
to fail.

The logic is a uniformity placebo. If the claim "corridor X sits at the 12th percentile of a 300-run
no-rewiring ensemble" is evidence of rewiring, then ordinary untreated dyads must land uniformly
inside that ensemble. We therefore compute, for every dyad present in both the actual panel and the
ensemble, the percentile of the actual weight within the 300 counterfactual draws, and we test the
resulting distribution against U[0,1].

It is not uniform. However, the departure is not marginal. Across roughly 2,653 comparable dyads in
the printed 2020 to 2024 window, the Kolmogorov-Smirnov distance to uniform is approximately 0.239,
with approximately 28.3% of dyads below the ensemble's 5th percentile and approximately 27.5% above
its 95th, against 5% expected at each tail. A 2017 to 2019 pre-period backtest is worse, returning a
KS distance of approximately 0.305 across roughly 2,928 dyads.

Of note, the cause is structural rather than a port bug, which matters because a bug would be
fixable and this is not. The generator's within-dyad dispersion is Equation 8 GDP jitter around an
initialized weight, at a median model standard deviation of approximately 0.104 dex, while real
dyads move approximately 0.421 dex cross-sectionally. The bands are therefore approximately 4.1x too
tight in the printed window and approximately 10.7x too tight in the pre-period. This translates to
a stark operational consequence: **a raw percentile of 12 is unremarkable when approximately 28% of
all dyads sit below 5.**

---

## E. The Correction

Our objective, having established that the instrument's own bands cannot carry inference, is to
achieve the original objective anyway. `analysis/72_empirical_null.py` rebuilds the null from the
cross-section rather than from the model, following Efron's empirical-null construction.

For each comparable dyad we compute a deviation, r equal to the base-10 log of the actual weight
over the ensemble median weight, measured in dex. We then ask where a named corridor's r sits in the
empirical distribution of r across all comparable dyads. The resulting statement reads "bottom X% of
all dyads by deviation from the GDP-implied benchmark", and it survives the over-tight bands because
it never uses them. The same script reports the over-dispersion factor, being cross-sectional
standard deviation over median within-dyad model standard deviation, which is the single number
quantifying how over-confident the raw percentile was.

Therefore the corrected readings for the printed window put China-US at approximately 0.86x the
benchmark median and roughly the 34th percentile of all dyads, with Mexico-US at approximately 0.94x
and roughly the 43rd. The connectors run the other way, with China-Vietnam at approximately 1.25x
and roughly the 75th and Vietnam-US at approximately 1.26x and roughly the 75th. Direction survives,
with China-US suppressed and the connectors elevated. Magnitudes are ordinary-large rather than
extreme.

Additionally, a dose-response check bounds the reading further. The pre-period backtest places
China-US at roughly the 21.8th empirical percentile in 2019 against roughly the 34.4th in 2024, so
most of the suppression predates the ensemble's start line, exactly as the 2020 initialization
predicts.

---

## F. What the Correction Costs

Our final methodological objective is to state what the repair does not buy, since a correction
presented without its price is a second overclaim.

The empirical null buys honesty at the cost of power. However, it takes its reference distribution
from the same cross-section that contains the treated corridors, so it cannot distinguish a targeted
shock from an ordinary large one and reports direction and rank rather than significance. A corridor
at the 34th percentile is not thereby shown to be treated, only shown to sit where it sits.
Conversely, the raw ensemble percentile had power it had not earned, which is the worse of the two
failures.

From this, two extensions follow directly. A dyad-level volatility model, in which each pair carries
its own dispersion rather than inheriting the generator's uniform Equation 8 jitter, would restore a
calibrated per-corridor null without discarding the generator. Percolating on edge subsets rather
than whole nodes would likewise close the gap between the attack curves and the way a state actually
re-prices trade. Both are natural extensions of this research, and neither is attempted here.

Lastly, one instrument boundary must be restated because an early draft of the paper crossed it.
The descriptive gravity fit that reports China-US at approximately 0.35x its GDP-implied weight is
a per-year ordinary-least-squares fit on directed flows anchored in 2017. It is **not** the
CompleNet counterfactual, which reports approximately 0.86x on undirected pair weights initialized
in 2020. Both readings are true, they measure against different baselines, and quoting them as one
figure is the specific error `notes/PLACEBO-FINDING-2026-07-31.md` was raised to catch.
