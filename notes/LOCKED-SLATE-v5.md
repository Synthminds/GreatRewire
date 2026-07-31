# LOCKED SLATE v5.0 ;  ten forecasts (2026-07-31 ~15:00 ET)

Supersedes LOCKED-SLATE-v4.md (+v4.1). Printed in `paper/forecasts.tex`.

| ID | P | Claim (short) | Resolves on | Reads |
|---|---|---|---|---|
| A1 | **62** | US avg effective tariff rate >8% cal-2027 | USITC DataWeb annual | edge re-pricing survives two legal defeats |
| A2 | **38** | BIS adds ≥100 China entities, Aug-26→Dec-27 | Federal Register final rules | a resumption bet ;  the freeze breaks with the truce |
| A3 | **45** | China extraterritorial mineral enforcement documented by end-27 | MOFCOM action | Beijing adopts Washington's weapon |
| B4 | **45** | (Mexico+ASEAN) − China ≥30pp of US goods imports, cal-2027 | US Census partner data | flows re-route first |
| B5 | **20** | China+HK ≥12% of NVIDIA revenue, FY2028 | FY28 10-K geographic table | severed max-weight edges don't re-heal (inverted) |
| C6 | **45** | Big-4 cal-2027 capex >$1.0T incl. finance leases | SEC EDGAR | the grab still accelerates toward its constraint |
| C7 | **75** | US data-center load >8% of generation, cal-2028 | LBNL over EIA | the power constraint approaches its binding point |
| C8 | **55** | ≥40 states with large-load tariffs by end-27 | EEI tracker + PUC orders | policy diffuses where the shadow price peaks |
| C9 | **42** | Big-4 capex YoY <10% two consecutive quarters before end-28 | Quarterly 10-K/10-Q | exponential demand meets linear infrastructure |
| D10 | **35** | CPS comp-math unemployment gap ≥1.5pp before end-27 | BLS LNU04034021 vs LNU04027662 | the network reprices its own builders first |

**Balance:** three at or above 55 (A1, C7, C8); seven below even. Mean 46.2, range 20–75.
Modal-outcome Brier 0.150, or approximately 40.0% better than a coin flip, computable live on the companion.

## What changed from v4.1, and why

The contest requires a **minimum of 10** binary forecasts (2026 event page), not exactly 10 ; 
verified live 2026-07-31. The cut to ten was made on merit, not compliance: the page cap was
binding at 10/10 and the placebo material needed room in the results.

**Dropped old B6**, meaning ≤5nm-class capacity outside Taiwan AND South Korea ≥25% by end-2028.
Our own audit (`notes/AUDIT-2026-07-30.md`, `notes/infra-evidence.md` §4) established that **no
public series exists for that metric**. It resolved on a company-disclosure fallback and the
"~5–10% today" figure was our own construction from disclosed fab capacities. A forecast that
cannot be adjudicated against a published series is the exact defect the rubric punishes.

**Dropped old D12**, meaning CIPS settlement value +50% cumulative cal-2025 to cal-2027. Weakest evidence
chain on the slate: the ¥180.2T base reaches us through China Daily *citing* CIPS Co (the annual
report PDF was never fetched), the +2.7% growth rate is calculated by us rather than published,
and the printed 35 overrode the model's own 28 on stated judgment alone. Also the most
thesis-distant entry ;  settlement rails are a lagging confirmation, not part of either grab.

**Renumbering.** Remaining IDs were made contiguous so the printed slate reads 1–10 with no gaps:
old C7 to C6, C8 to C7, C9 to C8, C10 to C9, D11 to D10. A1 through B5 remain unchanged. This is
the ONLY renumbering ever performed, and IDs are stable from v5.0 forward.

**Group structure.** A (3, policy) / B (2, physical) / C (4, AI) / D (1, slowest layer). Group B's
header changed from "three speeds" to "two speeds", since the capacity bet was the third speed.
Group D is now a single-forecast coda, retitled "the regime reaches the people who built it".

## Knock-on edits

- `paper/main.tex`: Part 1 heading "Ten Forecasts"; abstract "ten"; layer framing reordered by
  speed; slate-balance paragraph now states the two cuts and why; §4 B6/D12 sentences removed;
  Appendix A resolution conventions replaced the B6 fallback with a general rule; Appendix D's
  D12 judgment paragraph removed; §E Taiwan-strait sensitivity no longer names B6.
- **New §5, "The test that broke the chain"**, which promotes the placebo out of the appendix into
  the results. Appendix B4 collapsed into B3 as a numbers-only calibration record (this also removed a
  pre-existing collision between appendix label B4 and forecast B4).
- `analysis/60_exhibits.py`: Exhibit X2-L annotation no longer cites the raw 12-15th percentile.
  It now reads "bottom third of all dyads by deviation (empirical null)", consistent with §5.
- Companion rebuilt for ten: slate data, counters, filter label, group headers, layer framing.

## Page budget after the change

Part 1 1.08pp (cap 1.75) · Part 2 2.87pp (**hard cap 3.00**) · Part 3 5.45pp total, of which
references run roughly 1.77pp, leaving approximately 3.68pp of analysis against a recommended 5 ·
**total 10 pages, zero overfull boxes.**
