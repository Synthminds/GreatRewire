#!/usr/bin/env python3
"""Our fifth research objective seeks to expose every instrument behind the paper for
inspection. To achieve this objective we assemble demo/data.js here from the analysis outputs
alone, so the interactive companion and the printed paper read from one set of numbers.

Everything here traces to a file in data/processed/ or to a notes/ evidence
table. We hand-enter no numbers except the slate metadata block below, which
we transcribe from paper/forecasts.tex for the probabilities and from the verified
evidence notes for the current values, each carrying its own source and as-of label.
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data/processed"

# ---- slate: we take probabilities from paper/forecasts.tex and thresholds/currents from notes ----
SLATE = [
 dict(id="A1", g="A", p=62,
   q="US average effective tariff rate (duties ÷ customs value) exceeds 8% for calendar 2027",
   res="USITC DataWeb annual figures",
   reads="edge re-pricing survives two legal defeats",
   thr=8, unit="%", dir="up", cur=None,
   note="Live rate depends on method and vintage: 12.1% statutory average (Yale Budget Lab, Jul 21 2026) vs ~8.1% trade-weighted after the Feb 2026 ruling. The resolver pins one method, USITC duties over customs value, precisely because these diverge."),
 dict(id="A2", g="A", p=38,
   q="BIS adds ≥100 China-based entities to the Entity List in final rules citing semiconductor, advanced-computing or AI grounds, Aug 1 2026 – Dec 31 2027",
   res="Federal Register final rules; coding convention in Appendix A",
   reads="a resumption bet on the freeze breaking with the truce",
   thr=100, unit=" entities", dir="up", cur=0,
   note="Counting window opens Aug 1 2026, so the counter starts at zero by construction. Priced at 38 rather than the CNAS base rate because a documented 8-month listing freeze broke that base rate."),
 dict(id="A3", g="A", p=45,
   q="China's extraterritorial enforcement of its critical-mineral export controls is documented as applied to at least one foreign-made product by Dec 31 2027",
   res="MOFCOM enforcement announcement or documented license action",
   reads="Beijing adopts Washington's weapon",
   thr=None, unit="", dir="up", cur=None,
   note="Binary event, no running counter. Clock: the suspension of MOFCOM Announcements 55–58/61/62 runs to Nov 10 2026; Announcement 46 Art. 2 to Nov 27 2026."),
 dict(id="B4", g="B", p=45,
   q="Mexico plus ASEAN's combined share of US goods imports exceeds China's share by at least 30 percentage points in calendar 2027",
   res="US Census annual partner-level data",
   reads="flows re-route first; threshold re-armed above the +25.7pp YTD",
   thr=30, unit="pp", dir="up", cur=25.7, asof="YTD 2026, US Census"),
 dict(id="B5", g="B", p=20,
   q="China plus Hong Kong account for ≥12% of NVIDIA's total revenue in fiscal 2028",
   res="NVIDIA FY2028 10-K geographic table (customer-headquarters basis)",
   reads="severed maximum-weight edges do not re-heal (inverted)",
   thr=12, unit="%", dir="up", cur=9.1, asof="FY2026 10-K"),
 dict(id="C6", g="C", p=45,
   q="Combined calendar-2027 capex of Microsoft, Alphabet, Amazon and Meta, including finance leases, exceeds $1.0 trillion",
   res="10-K/10-Q disclosures including finance-lease additions, MSFT calendarized; SEC EDGAR",
   reads="the grab still accelerates toward its constraint",
   thr=1000, unit="B", pre="$", dir="up", curlo=700, curhi=725, asof="2026 guided",
   note="Gauge compares 2026 guided spending against a calendar-2027 threshold, so one year of growth has to happen inside the gap."),
 dict(id="C7", g="C", p=75,
   q="US data-center electricity consumption exceeds 8% of total US generation in calendar 2028",
   res="LBNL data-center series over EIA total net generation",
   reads="the power constraint approaches its binding point",
   thr=8, unit="%", dir="up", cur=4.7, asof="2024 actual, LBNL 2025 Update",
   note="≈6.5–7.8% in 2026 on LBNL's reference path, but that interpolation is ours, so the gauge shows the last published actual. LBNL reports share of consumption; C7 resolves on share of generation (≈5% larger denominator)."),
 dict(id="C8", g="C", p=55,
   q="At least 40 US states have approved data-center / large-load tariffs or equivalent large-load rules by Dec 31 2027",
   res="EEI large-load tariff tracker; state PUC final orders",
   reads="policy diffuses where the shadow price peaks",
   thr=40, unit=" states", dir="up", cur=24, asof="EEI, July 2026",
   note="24 approved plus 6 pending. EEI's own count moved 20 → 24 between March and July 2026, roughly one state a month, which is the pace the 55% is priced off."),
 dict(id="C9", g="C", p=42,
   q="Year-over-year growth of combined Big-4 hyperscaler capex falls below 10% in two consecutive quarters before Dec 31 2028",
   res="Quarterly 10-K/10-Q disclosures, same capex basis as C6",
   reads="exponential demand meets linear infrastructure",
   thr=10, unit="%", dir="down", cur=69.5, asof="latest quarter, YoY"),
 dict(id="D10", g="D", p=35,
   q="US unemployment for computer and mathematical occupations exceeds the all-college-graduate rate by ≥1.5pp in any calendar quarter before end-2027",
   res="BLS CPS LNU04034021 vs LNU04027662, not seasonally adjusted",
   reads="the network reprices its own builders first",
   thr=1.5, unit="pp", dir="up", cur=0.53, asof="2026Q2"),
]

def load_prev():
    s = (ROOT/"demo/data.js").read_text()
    return json.loads(s[s.index("=")+1:].rstrip().rstrip(";"))

prev = load_prev()
calib = json.loads((D/"calib_export.json").read_text())
enull = json.loads((D/"empirical_null.json").read_text())

out = {
  "slate": SLATE,
  "x1": prev["x1"],
  "attack": prev["attack"],
  "g": prev["g"],
  "cor": prev["cor"],
  "calib": calib,
  "enull": {"main": enull["main_2020_2024"], "pre": enull["pre_2017_2019"]},
}
js = "window.GR_DATA=" + json.dumps(out, separators=(",", ":")) + ";\n"
(ROOT/"demo/data.js").write_text(js)
print("wrote demo/data.js", len(js), "bytes | slate", len(out["slate"]),
      "| calib bins", len(calib["pct_hist"]["counts"]), "| corridors", len(out["cor"]))
