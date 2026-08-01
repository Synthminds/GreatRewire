# The Great Rewiring

[![verify](https://github.com/Synthminds/GreatRewire/actions/workflows/verify.yml/badge.svg)](https://github.com/Synthminds/GreatRewire/actions/workflows/verify.yml)

Two resource grabs, one network: pricing modern mercantilism and artificial intelligence on the
world trade web. Reproduction package for a submission to Bridgewater and Global Citizen,
*Forecasting the Future 2026*.

> ### Agents start here: **[AGENTS.md](AGENTS.md)**
> The capability table, the data contracts, and the four guardrails live in that file. A
> machine-readable mirror sits at [`.well-known/greatrewire.json`](.well-known/greatrewire.json).

Licence: MIT, code only. See the data note below.

---

## What This Is

This package treats the world trade network as one object and prices two simultaneous grabs against
it. The first is mercantilist, contesting chokepoints in semiconductors, critical minerals,
batteries, pharmaceutical ingredients, and aerospace. The second is computational, contesting power,
capital, and silicon. The two grabs land on one object rather than two.

The instrument shared across both is a synthetic generator of the world trade web, published at
CompleNet 2022. Feed it nothing but each country's GDP and it reproduces who trades with whom, how
densely, and through which hubs. We port it to Python, validate it against its own reported
statistics, then run it forward as a null for a world that never rewired.

The repository holds that generator, the experiments run on it, the audits that broke one of them,
the correction that followed, and the ten binary forecasts the whole apparatus supports. It does not
hold the paper.

---

## What It Found

Findings are numbered in [`docs/FINDINGS.md`](docs/FINDINGS.md) with the conditions attached to
each. Four carry the argument.

**The port is faithful.** Run across 1996 to 2020 under the published log-normal GDP conditions, the
ported generator reproduces six headline statistics from the published tables within approximately
2.9%. Those are the conditions the published Table 2 was itself generated under, which is why
validating against it requires them. That gives us a null we can run forward without having smuggled
our own discretion into it.

**Targeted removal partitions value where random failure does not.** Removing the strongest 10% of
countries from the actual 2024 network leaves approximately 8.4% of original trade weight in the
surviving connected component, against approximately 83.7% under random failure of the same
magnitude. The topology holds and the value structure partitions. That is a roughly tenfold gap
between an adversary who chooses and an accident that does not.

**The counterfactual bands failed their own placebo.** Pushing roughly 2,653 comparable country pairs
through the 300-run ensemble should return approximately uniform percentiles. It returns
approximately 28.3% below the 5th percentile and approximately 27.5% above the 95th, at a
Kolmogorov-Smirnov distance to uniform of approximately 0.239. The generator's within-pair
dispersion of approximately 0.104 dex sits against a real cross-section of approximately 0.421 dex,
where one dex is a factor of ten. The bands run approximately 4.1 times too tight, and roughly 10.7
times too tight in the 2017 to 2019 pre-period.

**Corrected, the direction survives and the magnitude does not.** Rebuilding the null from the
cross-section of deviations, following Efron, puts the China-US corridor at approximately 0.86 times
its benchmark median and roughly the 34th percentile of all comparable country pairs. The Vietnam-US
corridor runs the other way, at approximately 1.26 times and roughly the 75th. Suppression and
re-routing are both real, and both are ordinary-large rather than extreme.

The last two findings are the point of the package rather than a blemish on it. A forecaster who
placebo-tests his own null, finds it over-confident by a factor of four, and prints the correction
has produced a more useful instrument than one who never looked.

---

## The Ten Forecasts

The slate is locked at v5.0 and recorded in [`notes/LOCKED-SLATE-v5.md`](notes/LOCKED-SLATE-v5.md).
IDs A1 through D10 are stable and will not be renumbered.

The four groups are four speeds of response to the same shock. Governments move first, deleting and
re-pricing trade routes within quarters (A). Trade flows re-route behind them over quarters to years
(B). The AI buildout answers on construction time, because transformers, transmission lines, and
generation take years to build (C). Labor moves last (D).

| ID | P | Claim (short) |
|---|---|---|
| A1 | 62 | US average effective tariff rate above 8% for calendar 2027 |
| A2 | 38 | BIS adds 100 or more China entities, Aug-26 through Dec-27 |
| A3 | 45 | China extraterritorial mineral enforcement documented by end-27 |
| B4 | 45 | (Mexico plus ASEAN) minus China at 30pp or more of US goods imports, cal-2027 |
| B5 | 20 | China and Hong Kong at 12% or more of NVIDIA revenue, FY2028 |
| C6 | 45 | Big-4 cal-2027 capex above $1.0T including finance leases |
| C7 | 75 | US data-center load above 8% of generation, cal-2028 |
| C8 | 55 | 40 or more states with large-load tariffs by end-27 |
| C9 | 42 | Big-4 capex YoY below 10% for two consecutive quarters before end-28 |
| D10 | 35 | CPS computer-and-mathematical unemployment gap at 1.5pp or more before end-27 |

*Source: Author (2026).*

Three sit at or above 55 and seven below even, with a mean of 46.2 across a range of 20 to 75. The
modal-outcome Brier score is 0.150, which assumes every forecast resolves in the direction it leans
and is therefore a statement of confidence rather than skill. Scored against our own probabilities,
the expected Brier score is approximately 0.23.

---

## How to Rerun

Python 3.11 with the packages in [`requirements.txt`](requirements.txt). Every script fixes its
seeds, so reruns are deterministic. For exact reproduction of the printed figures,
[`requirements.lock`](requirements.lock) pins the environment the results were verified in.

```bash
pip install -r requirements.txt

# 0. Confirm the generator, which needs no trade data at all
python3 models/wtw_model.py                      # equation self-test, under 5 seconds -> ALL PASS
python3 models/validate_completnet.py            # port validation -> VERDICT: PASS (6/6)

# 1. Build the trade panel. This gates almost everything below.
python3 analysis/10_baci_aggregate.py            # downloads CEPII BACI, see the data note
python3 analysis/20_multigraph.py                # five strategic-sector layers

# 2. The experiments
python3 analysis/40_counterfactual.py            # 300-run no-rewiring ensemble, 2 to 4 minutes
python3 analysis/41_attack.py                    # attack percolation

# 3. The audits, in order. 71 breaks 40's bands and 72 repairs them.
python3 analysis/70_rf_rigor.py                  # random-forest out-of-sample checks
python3 analysis/71_placebo.py                   # uniformity placebo, 6 to 10 minutes
python3 analysis/72_empirical_null.py            # the Efron correction, 6 to 10 minutes
python3 analysis/73_calib_export.py              # calibration export
```

`validate_completnet.py` defaults to the paper's own log-normal GDP conditions, which is the mode
Table 2 was generated under and therefore the only mode that can validate against it. It prints
`VERDICT: PASS (6/6)` and regenerates `data/processed/port_validation.csv` with data rows identical
to the committed copy. The `--mode real` flag drives the same port with actual World Bank GDPs; that
path is a diagnostic and does not clear the Table 2 contract.

The ordering within step 3 is not cosmetic. Reading `72_empirical_null.py` output without having
seen `71_placebo.py` fail first invites exactly the misreading that guardrail G2 in
[`AGENTS.md`](AGENTS.md) forbids.

---

## What Is Deliberately Absent

This repository ships what a reader or an agent needs to understand and rerun the work, and nothing
that merely documents how it was made. Six categories are absent by decision rather than by
oversight.

**Raw CEPII BACI HS17 V202601.** The licence does not permit redistribution. Download it from
cepii.fr and `analysis/10_baci_aggregate.py` regenerates everything downstream.

**The bilateral trade panel.** `wtw_agg_2017_2024.csv` is a direct aggregation of BACI values at
roughly 5.6 MB, so it falls under the same restriction and under the size discipline this repository
holds itself to. It rebuilds in one command.

**The `0x` data-pull scripts.** They require API keys and network access to eight separate
providers, so a third party cannot reproduce them as written. Their outputs ship instead, each
carrying a provenance header naming the source, the pull date, and the units.

**The exhibit-rendering and Monte Carlo scripts.** `60_exhibits.py`, `61_x1_redesign.py`,
`21_actuals_metrics.py`, `22_x3_envelope.py`, and `50_mc_finals.py` produce the figures and the
draft forecast posteriors. The rendered figures ship in [`figures/`](figures); the code that styles
them adds nothing a reader needs.

**The LaTeX sources.** This is the machinery, not the paper.

**Internal working notes.** Fourteen notes covering evidence tables, audit logs, adversarial review,
and superseded slate versions live in the private repository. The three that a reader needs to judge
the work ship in [`notes/`](notes): the locked slate, the placebo finding, and the dated rationale for
the one printed probability that differs most from its model draft.

---

## Documentation

| File | Contents |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Capability table, determinism notes, data contracts, guardrails, worked example |
| [`docs/METHOD.md`](docs/METHOD.md) | The generator, the null, the calibration failure, and its correction |
| [`docs/DATA.md`](docs/DATA.md) | Every source, its vintage, its licence, and what is not redistributed |
| [`docs/FINDINGS.md`](docs/FINDINGS.md) | The numbered results with the conditions under which each holds |

*Source: Author (2026).*

---

## Provenance

### Declaration of AI use

During the preparation of this work we used ChatGPT, Claude, Perplexity, and GPAI. We used them to
expand the option space, generating alternative framings and counterarguments for us to evaluate. We
used them to surface candidate patterns across studies and datasets, each of which we then checked
against the sources ourselves. We also used them to challenge our assumptions and to hunt for gaps
and bias in our own reasoning, and to improve readability. They assisted in writing and debugging the
Python that builds the panel, runs the counterfactual ensembles, and produces the exhibits. We
verified every output, result, and line of code against the underlying data and against established
method before it entered this paper. No probability, threshold, resolution criterion, or conclusion
here was set by a model. We reviewed and edited all content, we take full responsibility for it, and
the ideas put forward are our own.

This declaration appears verbatim in the paper's front matter.

### What that means for this repository

All models were designed and run by the author. All probabilities were set by the author in a
verification pass held separate from model construction. The private repository carries the full
decision log, including the two places where an early draft overclaimed and was corrected before
print.

## Citation

See [`CITATION.cff`](CITATION.cff).

## Contact

For questions, data access, or the private repository: wes@synthminds.ai
