# LOCKED SLATE v5.0: Ten Forecasts (2026-07-31, approximately 15:00 ET)

Supersedes LOCKED-SLATE-v4.md and v4.1, and is printed in the paper's forecast table. Pointers in
this record to files not present here, such as `paper/forecasts.tex` and the evidence notes, refer
to the private research repository.

| ID | P | Claim (short) | Resolves on | Reads |
|---|---|---|---|---|
| A1 | **62** | US avg effective tariff rate >8% cal-2027 | USITC DataWeb annual | edge re-pricing survives two legal defeats |
| A2 | **38** | BIS adds >=100 China entities, Aug-26 through Dec-27 | Federal Register final rules | a resumption bet, where the freeze breaks with the truce |
| A3 | **45** | China extraterritorial mineral enforcement documented by end-27 | MOFCOM action | Beijing adopts Washington's weapon |
| B4 | **45** | (Mexico+ASEAN) minus China >=30pp of US goods imports, cal-2027 | US Census partner data | flows re-route first |
| B5 | **20** | China+HK >=12% of NVIDIA revenue, FY2028 | FY28 10-K geographic table | severed max-weight edges do not re-heal (inverted) |
| C6 | **45** | Big-4 cal-2027 capex >$1.0T incl. finance leases | SEC EDGAR | the grab still accelerates toward its constraint |
| C7 | **75** | US data-center load >8% of generation, cal-2028 | LBNL over EIA | the power constraint approaches its binding point |
| C8 | **55** | >=40 states with large-load tariffs by end-27 | EEI tracker + PUC orders | policy diffuses where the shadow price peaks |
| C9 | **42** | Big-4 capex YoY <10% two consecutive quarters before end-28 | Quarterly 10-K/10-Q | exponential demand meets linear infrastructure |
| D10 | **35** | CPS comp-math unemployment gap >=1.5pp before end-27 | BLS LNU04034021 vs LNU04027662 | the network reprices its own builders first |

**Balance:** three at or above 55 (A1, C7, C8), and seven below even. Mean 46.2, range 20 to 75.
Modal-outcome Brier 0.150, which is 40.0% better than a coin flip and computable live on the
companion.

## What Changed From v4.1, and Why

The contest requires a **minimum of 10** binary forecasts per the 2026 event page, not exactly 10,
verified live on 2026-07-31. However, the cut to ten was made on merit rather than on compliance.
The page cap was binding at 10 of 10 and the placebo material needed room in the results.

**Dropped old B6**, which claimed 5nm-class-or-finer capacity outside Taiwan AND South Korea at
25% or more by end-2028. Our own audit established that **no public series exists for that
metric**. It resolved on a company-disclosure fallback, and the "approximately 5 to 10% today"
figure was our own construction from disclosed fab capacities. A forecast that cannot be
adjudicated against a published series is the exact defect the rubric punishes.

**Dropped old D12**, which claimed CIPS settlement value up 50% cumulatively from cal-2025 to
cal-2027. It carried the weakest evidence chain on the slate. The 180.2T yuan base reaches us
through China Daily *citing* CIPS Co, since the annual report PDF was never fetched, the +2.7%
growth rate is calculated by us rather than published, and the printed 35 overrode the model's own
28 on stated judgment alone. It was also the most thesis-distant entry, since settlement rails are
a lagging confirmation rather than part of either grab.

**Renumbering.** Remaining IDs were made contiguous so the printed slate reads 1 through 10 with
no gaps: old C7 became C6, C8 became C7, C9 became C8, C10 became C9, and D11 became D10. A1
through B5 are unchanged. This is the ONLY renumbering ever performed, and IDs are stable from
v5.0 forward.

**Group structure.** A carries three policy forecasts, B two physical, C four AI, and D one at the
slowest layer. Group B's header changed from "three speeds" to "two speeds", since the capacity
bet was the third speed. Group D is now a single-forecast coda, retitled "the regime reaches the
people who built it".

## Knock-On Edits

- `paper/main.tex`: Part 1 heading became "Ten Forecasts", the abstract now reads "ten", and the
  layer framing is reordered by speed. The slate-balance paragraph now states the two cuts and why,
  and the section 4 B6 and D12 sentences were removed. Appendix A resolution conventions replaced
  the B6 fallback with a general rule, Appendix D's D12 judgment paragraph was removed, and the
  Taiwan-strait sensitivity no longer names B6.
- **New section 5, "The test that broke the chain"**, promoting the placebo out of the appendix
  and into the results. Appendix B4 collapsed into B3 as a numbers-only calibration record, which
  also removed a pre-existing collision between appendix label B4 and forecast B4.
- `analysis/60_exhibits.py`: the Exhibit X2-L annotation no longer cites the raw 12th to 15th
  percentile. It now reads "bottom third of all dyads by deviation (empirical null)", consistent
  with section 5.
- Companion rebuilt for ten forecasts across the slate data, counters, filter label, group
  headers, and layer framing.

## Page Budget After the Change

Part 1 runs 1.07pp against a 1.75 cap, Part 2 runs 2.87pp against a **hard cap of 3.00**, and
Part 3 runs 5.47pp in total, of which references take 1.77pp, leaving analysis 3.70pp against a
recommended ceiling of 5. **Total 10 pages, zero overfull boxes.**
