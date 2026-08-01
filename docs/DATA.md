# DATA

Every source behind the analysis, its vintage, its licence, and what this repository does not
redistribute.

---

## 1. Reading the Provenance Headers

Every shipped file is self-describing, so a reader who opens one in isolation can establish where it
came from without consulting this document.

Therefore every CSV under `data/processed/` opens with one or more comment lines beginning with `#`.
Those lines name the upstream source, the pull date, the producing script, and the units.
The units line is not decorative. Trade weights arrive in thousands of US dollars, capital
expenditure in dollars, GDP in dollars for World Bank series and in billions for IMF series,
generation in terawatt-hours, and unemployment gaps in percentage points. Mixing them silently is
the most likely way to produce a wrong number from correct files. Every reader in the repository
passes `comment="#"` for this reason.

The licence characterisations below are our reading of each provider's published terms as of
July 2026. They are not legal advice, and a party intending to redistribute any of this
material should verify the current terms at the source before doing so.

---

## 2. Primary Network Source

| Field | Value |
|---|---|
| Source | CEPII BACI, HS 2017 nomenclature, release V202601 |
| What it provides | Bilateral trade values and quantities at the HS6 product level, roughly 11 million records per year |
| Vintage | V202601, covering 2017 through 2024 |
| Access | https://www.cepii.fr/DATA_DOWNLOAD/baci/data/BACI_HS17_V202601.zip |
| Licence | Etalab Open Licence 2.0, the CEPII open licence, which requires attribution |
| Redistributed here | **No.** See section 5. |
| Consumed by | `analysis/10_baci_aggregate.py`, and through its output by everything downstream |

*Source: Author (2026).*

BACI ships Taiwan under code 490, "Other Asia, nes", with no usable ISO3 label.
`analysis/10_baci_aggregate.py` therefore emits an `iso3_recode` column mapping 490 to TWN, and
every downstream script reads the recoded column. Taiwan therefore appears as a first-class
node in the semiconductor layer, which the analysis would otherwise be unable to
discuss.

---

## 3. Macroeconomic and Policy Series

| Source | Series or endpoint | Vintage | Licence | Shipped file |
|---|---|---|---|---|
| World Bank WDI | `NY.GDP.MKTP.CD`, GDP in current US dollars, 1995 to 2024 | API `lastupdated` 2026-07-13, pulled 2026-07-30 | CC BY 4.0 under World Bank open data terms | `wdi_gdp_1995_2024.csv` |
| IMF World Economic Outlook | `NGDPD` via DataMapper API v1, GDP in billions of current US dollars | WEO April 2026 vintage, pulled 2026-07-30 | IMF terms permit derived redistribution with attribution | `imf_weo_ngdpd_2020_2028.csv` |
| US Census Bureau | FT900 country workbook, general imports, Census basis, not seasonally adjusted | Pulled 2026-07-30 | US Government work, public domain | `us_import_shares.csv` |
| SEC EDGAR XBRL | `companyconcept` capital-expenditure facts for MSFT, GOOGL, AMZN, META | Pulled 2026-07-30 | US Government work, public domain | `big4_capex_quarterly.csv`, `big4_capex_combined_quarterly.csv` |
| SEC EDGAR submissions | CIK 0001045810, NVIDIA filing index | Pulled 2026-07-30 | US Government work, public domain | `nvda_filings_manual.csv` |
| US EIA | Monthly Energy Review Table 7.2a, MSN `ELETPUS`, electricity net generation | Pulled 2026-07-30 | US Government work, public domain | `eia_net_generation_twh.csv` |
| US BLS | CPS series `LNU04034021` and `LNU04027662`, not seasonally adjusted | Pulled 2026-07-30 | US Government work, public domain | `cps_unemp_gap_quarterly.csv` |
| Federal Register | API v1, Bureau of Industry and Security final rules matching "entity list" from 2024-01-01 | Pulled 2026-07-30 | US Government work, public domain | `bis_entity_rules_2024_2026.csv` |

*Source: Author (2026).*

Two entries in that table carry a caveat that the file itself also states. The BIS rules file
records one row per final rule, and the per-rule entity counts are a manual coding pass rather than
a parsed field, so the count supporting forecast A2 is our reading of the rules rather than a
published figure. The NVIDIA file is likewise a manual-read index, because the China
revenue share lives in the geographic-segment note rather than in a tagged XBRL concept. Both are
conceded here rather than in a footnote, and automating either would extend this
work.

---

## 4. Cited but Not Ingested

Four further sources inform the forecast slate through transcribed constants rather than through a
pull script, and none of them is redistributed. Lawrence Berkeley National Laboratory's 2025 Update
to the data-center energy report, published June 2026, and its Queued Up 2026 interconnection
analysis, published July 2026, supply the data-center load constants used in `x3_inputs.csv` and
in forecast C7. The Edison Electric Institute large-load tariff tracker, as of July 2026, supplies
the state count behind forecast C8. The Center for a New American Security supplies the Entity List
base rate that forecast A2 prices against and then departs from. Publications by CIPS and SWIFT
informed a settlement-rails forecast that was cut at slate v5.0, and the reasoning behind that cut
is recorded in `notes/LOCKED-SLATE-v5.md`.

Each of these is a published document under its own terms. We cite them, transcribe
specific figures with an as-of label attached, and redistribute none of them.

---

## 5. What We Do Not Redistribute

The boundary is stated explicitly, since a reader who assumes a missing file is an oversight will
waste effort looking for it.

**Raw CEPII BACI.** Neither the HS6 archive, nor `baci_2024_hs6.parquet` at roughly 109 MB, nor
`baci_country_codes.csv` appears here. The CEPII licence governs the raw distribution and requires
that users obtain it from CEPII directly. Running `analysis/10_baci_aggregate.py` downloads it and
regenerates all three files.

**The bilateral trade panel.** `wtw_agg_2017_2024.csv`, at roughly 5.6 MB, is a direct aggregation
of BACI values with no transformation beyond summation over products. It therefore falls on the
restricted side of the same boundary, and it also exceeds the size discipline this repository
holds itself to. It is the single hard precondition for most of the pipeline, and section 3 of
`AGENTS.md` states which capabilities it gates.

**Raw pull artifacts.** The `data/raw/` directory in the private repository holds
roughly 5.4 MB of provider responses, including a Census workbook, an EIA monthly series, and
several EDGAR JSON payloads. They are omitted because each is reproducible from a public endpoint
and none is needed to rerun the analysis.

**Derived files whose producers are absent.** `mc_finals.csv`, holding draft Monte Carlo posteriors
for the forecast slate, is omitted because its producing script is not shipped and because the
locked slate in `notes/LOCKED-SLATE-v5.md` supersedes it as the authoritative record.
`x3_inputs.csv` **is** shipped despite its producer being absent, because it is the provenance
trail for a figure that ships in `figures/`.

---

## 6. What Is Shipped

| File | Rows or shape | Produced by | Units |
|---|---|---|---|
| `actuals_metrics.csv` | long form, `block`/`metric`/`period`/`entity`/`value`/`unit` | `analysis/21_actuals_metrics.py` (not shipped) | per-row `unit` column |
| `attack_curves.csv` | 3 strategies by 3 metrics by 21 fractions | `analysis/41_attack.py` | dimensionless shares |
| `counterfactual_corridors.csv` | 9 corridors by 8 years by 2 kinds | `analysis/40_counterfactual.py` | model units, kappa scale |
| `counterfactual_ensemble.csv` | aggregate metrics by year | `analysis/40_counterfactual.py` | mixed, see `metric` column |
| `port_validation.csv` | 25 years, 1996 to 2020 | `models/validate_completnet.py` | dimensionless graph statistics |
| `placebo_results.json` | 2 windows | `analysis/71_placebo.py` | percentiles in [0,1], KS dimensionless |
| `empirical_null.json` | 2 windows | `analysis/72_empirical_null.py` | deviations in dex, percentiles in [0,1] |
| `calib_export.json` | 2 histograms plus markers | `analysis/73_calib_export.py` | as above |
| `multigraph/*_edges.csv` | 5 sector layers, directed | `analysis/20_multigraph.py` | thousands of current USD |
| `multigraph/chokepoint_table.csv` | top 10 per layer per metric | `analysis/20_multigraph.py` | ranks and shares |
| `multigraph/x1_nodes_edges.json` | approximately 30 nodes, top 15 edges per layer | `analysis/20_multigraph.py` | thousands of current USD |
| `wdi_gdp_1995_2024.csv` | country by year | `analysis/01_pull_wdi.py` (not shipped) | current US dollars |
| `imf_weo_ngdpd_2020_2028.csv` | economy by year | `analysis/02_pull_weo.py` (not shipped) | billions of current US dollars |
| `us_import_shares.csv` | period rows | `analysis/08_pull_census_imports.py` (not shipped) | millions USD and percentage points |
| `big4_capex_quarterly.csv` | company by quarter | `analysis/03_pull_sec_capex.py` (not shipped) | US dollars per quarter |
| `big4_capex_combined_quarterly.csv` | quarter rows | `analysis/03_pull_sec_capex.py` (not shipped) | US dollars per quarter |
| `cps_unemp_gap_quarterly.csv` | quarter rows | `analysis/06_pull_bls_cps.py` (not shipped) | percent, gap in percentage points |
| `eia_net_generation_twh.csv` | period rows | `analysis/07_pull_eia_generation.py` (not shipped) | terawatt-hours |
| `bis_entity_rules_2024_2026.csv` | one row per final rule | `analysis/05_pull_bis_rules.py` (not shipped) | counts, manual coding pass |
| `nvda_filings_manual.csv` | filing index | `analysis/04_pull_nvda_filings.py` (not shipped) | not applicable |
| `x3_inputs.csv` | exhibit inputs | `analysis/22_x3_envelope.py` (not shipped) | mixed, see header |

*Source: Author (2026).*

Where the producing script is marked not shipped, the file's own provenance header carries
the endpoint, the query parameters, and the pull date, so a party with the relevant API access can
reconstruct it. Full column-level contracts for the files an agent is most likely to parse appear in
section 6 of `AGENTS.md`.

---

## 7. Citation Obligations

Any reuse of the derived trade tables must credit CEPII BACI HS17 V202601 as the underlying source,
because every trade weight in this repository descends from it. World Bank and IMF series carry
their own attribution requirements. United States federal sources, being works of the US
government, carry none, though naming them remains the honest practice and this repository does so
in every affected file header.
