# AGENTS.md

The agent entry point for **The Great Rewiring**. An agent that reads this file end to end should
therefore be able to run every capability in the repository, read every output correctly, and avoid
the four mistakes that would misrepresent the work. No human explanation is required beyond this
document.

---

## 1. What This Repository Is For

This package prices two simultaneous resource grabs, modern mercantilism and artificial
intelligence, on a single object: the world trade network. The question the repository
answers is narrow and testable. **Given a generator that explained the last twenty-five years of the
world trade web, how far has the actual 2021 to 2024 network diverged from the world that generator
would have produced had nothing rewired? Is that divergence large enough to be worth a name?**

The answer, stated in advance so no agent has to reconstruct it, is qualified. Direction
survives and magnitude does not. The China-US corridor sits at approximately 0.86x its GDP-implied
benchmark median, which is roughly the 34th percentile of all comparable country pairs, while the Vietnam
connector sits at approximately 1.26x, roughly the 75th. Those are the corrected readings.
The uncorrected readings from the generator's own percentile bands run approximately
4.1x too confident and must not be quoted as p-values. Section 7 of this file is the guardrail that
enforces that.

This repository is the reproduction package for a submission to Bridgewater and Global
Citizen, *Forecasting the Future 2026*. It is not the paper. It is the machinery underneath it.

---

## 2. Repository Map

| Path | What lives here |
|---|---|
| `models/` | The CompleNet 2022 synthetic world-trade-web generator, ported to Python, plus its validation harness. |
| `analysis/` | The numbered pipeline. Lower numbers build data, the 4x band runs experiments, the 7x band audits them. |
| `data/processed/` | Derived tables and JSON results. Every file carries a commented provenance header. |
| `data/processed/multigraph/` | Per-sector directed edge lists, chokepoint tables, and concentration measures for five strategic layers. |
| `figures/` | The four exhibit PDFs referenced by the paper. |
| `docs/` | Method, data provenance, and the numbered findings, in prose. |
| `notes/` | The locked forecast slate and the placebo finding, preserved as dated records. |
| `.well-known/` | `greatrewire.json`, a machine-readable mirror of the capability table and guardrails below. |

*Source: Author (2026).*

The repository deliberately omits several things a reader might expect. The `0x` data-pull
scripts, the raw BACI archive, the exhibit-rendering scripts, and the LaTeX sources are all absent,
and section 5 of `docs/DATA.md` explains each omission. The most consequential absence is
the bilateral trade panel itself, which section 3 addresses first for that reason.

---

## 3. Capability Table

Every command below is run from the repository root with Python 3.11. Runtimes marked *(measured)*
come from the scripts' own instrumentation. Runtimes marked *(estimated)* are
order-of-magnitude guidance and an agent should not treat them as a timeout contract.

| # | Capability | Entry point | Command | Reads | Writes | Runtime |
|---|---|---|---|---|---|---|
| C1 | Build the trade panel | `analysis/10_baci_aggregate.py` | `python3 analysis/10_baci_aggregate.py [--keep-zip]` | CEPII BACI HS17 V202601 zip, downloaded on demand from cepii.fr | `data/processed/wtw_agg_2017_2024.csv`, `baci_2024_hs6.parquet`, `baci_country_codes.csv` | approximately 20 to 40 minutes including the download *(estimated)* |
| C2 | Build the sector multigraph | `analysis/20_multigraph.py` | `python3 analysis/20_multigraph.py` | `baci_2024_hs6.parquet`, `baci_country_codes.csv`, `wtw_agg_2017_2024.csv` | 8 CSVs and 1 JSON under `data/processed/multigraph/` | approximately 3 to 8 minutes *(estimated)* |
| C3 | Validate the generator port | `models/validate_completnet.py` | `python3 models/validate_completnet.py --iters 30 --seed 42` (defaults to `--mode bootstrap`, the validated path) | nothing in bootstrap mode; `wdi_gdp_1995_2024.csv` in `--mode real` | `data/processed/port_validation.csv` | approximately 5 to 12 minutes *(estimated)* |
| C4 | Run the counterfactual ensemble | `analysis/40_counterfactual.py` | `python3 analysis/40_counterfactual.py` | `wtw_agg_2017_2024.csv`, `wdi_gdp_1995_2024.csv`, `imf_weo_ngdpd_2020_2028.csv` | `counterfactual_ensemble.csv`, `counterfactual_corridors.csv` | approximately 2 to 4 minutes *(measured)* |
| C5 | Run the attack percolation | `analysis/41_attack.py` | `python3 analysis/41_attack.py` | `wtw_agg_2017_2024.csv` | `data/processed/attack_curves.csv` | approximately 2 to 5 minutes *(estimated)* |
| C6 | Run the random-forest checks | `analysis/70_rf_rigor.py` | `python3 analysis/70_rf_rigor.py` | `wtw_agg_2017_2024.csv`, `wdi_gdp_1995_2024.csv` | `figures/x4_validation.pdf`, plus printed statistics | approximately 3 to 8 minutes *(estimated)* |
| C7 | Run the uniformity placebo | `analysis/71_placebo.py` | `python3 analysis/71_placebo.py` | `wtw_agg_2017_2024.csv`, `wdi_gdp_1995_2024.csv` | `data/processed/placebo_results.json` | approximately 6 to 10 minutes *(measured)* |
| C8 | Run the empirical-null correction | `analysis/72_empirical_null.py` | `python3 analysis/72_empirical_null.py` | `wtw_agg_2017_2024.csv`, `wdi_gdp_1995_2024.csv` | `data/processed/empirical_null.json` | approximately 6 to 10 minutes *(estimated, two ensembles)* |
| C9 | Export calibration data | `analysis/73_calib_export.py` | `python3 analysis/73_calib_export.py` | `wtw_agg_2017_2024.csv`, `wdi_gdp_1995_2024.csv` | `data/processed/calib_export.json` | approximately 3 to 5 minutes *(estimated, one ensemble)* |
| C11 | Self-test the generator | `models/wtw_model.py` | `python3 models/wtw_model.py` | nothing | nothing, prints `ALL PASS` | under 5 seconds *(measured)* |

*Source: Author (2026).*

The table carries one hard precondition that governs almost all of it. **C1 gates C2, C4,
C5, C6, C7, C8, and C9**, because `wtw_agg_2017_2024.csv` is the panel every one of them reads and
this repository does not ship it. Section 6 of `docs/DATA.md` states why. Therefore an agent that
attempts C4 without first completing C1 will fail on a missing-file error rather than on anything
subtle. C3, C9, and C11 run against files that do ship, so an agent with no BACI access can still
validate the port, export the calibration record, and confirm the generator's equations.

---

## 4. Suggested MCP Tool Surface

The surface below maps one to one onto the capability table, so that turning this repository into a Model Context Protocol server requires
scheduling and error handling rather than design. Types below follow JSON Schema conventions. Of
note, all paths returned are repository-relative POSIX paths, all durations are seconds, and all
monetary values are current US dollars unless a field name says otherwise.

Every tool shares two response envelope fields, omitted from the individual specifications for
brevity: `ok` (boolean) and `log_tail` (string, the final approximately 40 lines of stdout).

### 4.1 `build_trade_panel` (capability C1)

```jsonc
{
  "name": "build_trade_panel",
  "description": "Download CEPII BACI HS17 V202601 and aggregate roughly 11 million HS6 records per year into the bilateral panel every downstream tool reads. Long-running and network-bound.",
  "inputs": {
    "keep_zip":      { "type": "boolean", "default": false, "description": "Retain the downloaded BACI archive under data/raw/ instead of deleting it after a successful run." },
    "force_rebuild": { "type": "boolean", "default": false, "description": "Rebuild even when the panel already exists." }
  },
  "returns": {
    "panel_path":    { "type": "string",  "description": "Path to wtw_agg_2017_2024.csv." },
    "parquet_path":  { "type": "string",  "description": "Path to baci_2024_hs6.parquet." },
    "rows":          { "type": "integer", "description": "Row count of the bilateral panel." },
    "years":         { "type": "array", "items": { "type": "integer" }, "description": "Calendar years present, expected 2017 through 2024." },
    "duration_s":    { "type": "number" }
  },
  "side_effects": "Writes three files under data/processed/. Downloads roughly 1 GB over HTTPS.",
  "guardrail": "The returned parquet and country-code files must never be re-served or re-uploaded. See section 7."
}
```

### 4.2 `build_sector_multigraph` (capability C2)

```jsonc
{
  "name": "build_sector_multigraph",
  "description": "Build five strategic-sector layers from BACI 2024 HS6 flows and emit chokepoint, concentration, and rank tables.",
  "inputs": {
    "layers": { "type": "array", "items": { "type": "string", "enum": ["semiconductors","critical_minerals","batteries","pharma_apis","aerospace"] }, "default": "all five", "description": "Subset of sector layers to build." },
    "de_minimis_kusd": { "type": "number", "default": 1.0, "description": "Edges below this value in thousands of USD are omitted before graph construction." }
  },
  "returns": {
    "edge_files":       { "type": "object", "additionalProperties": { "type": "string" }, "description": "Layer name to edge-list path." },
    "chokepoint_table": { "type": "string", "description": "Path to chokepoint_table.csv." },
    "x1_graph":         { "type": "string", "description": "Path to x1_nodes_edges.json, the exhibit input." },
    "duration_s":       { "type": "number" }
  }
}
```

### 4.3 `validate_generator` (capability C3)

```jsonc
{
  "name": "validate_generator",
  "description": "Run the ported CompleNet 2022 generator across 1996 to 2020 under the paper's own bootstrapped log-normal GDP conditions, the same conditions its Table 2 was generated under, and compare yearly-average statistics against the published Table 1 and Table 2 anchors.",
  "inputs": {
    "iters": { "type": "integer", "default": 30, "minimum": 1, "description": "Independent model iterations averaged before comparison." },
    "seed":  { "type": "integer", "default": 42, "description": "Base seed. Iteration i uses seed + i." },
    "mode":  { "type": "string", "enum": ["real","bootstrap"], "default": "bootstrap", "description": "bootstrap regenerates the paper's own log-normal generating conditions and is the validated path, because Table 2 was itself produced under them. real drives the model with WDI GDPs and is a diagnostic; it does not clear the Table 2 contract." }
  },
  "returns": {
    "verdict":       { "type": "string", "enum": ["PASS","FAIL"], "description": "PASS requires the six headline statistics within approximately 5% of the Table 2 averages and k-core within plus or minus 10." },
    "max_deviation_pct": { "type": "number", "description": "Largest absolute percentage deviation across the compared statistics. The shipped run, in the default bootstrap mode, returns approximately 3.5 and a PASS." },
    "per_stat":      { "type": "array", "items": { "type": "object", "properties": { "stat": {"type":"string"}, "port": {"type":"number"}, "published": {"type":"number"}, "deviation_pct": {"type":"number"} } } },
    "csv_path":      { "type": "string", "description": "Path to port_validation.csv, one row per year 1996 through 2020." },
    "duration_s":    { "type": "number" }
  }
}
```

### 4.4 `run_counterfactual_ensemble` (capability C4)

```jsonc
{
  "name": "run_counterfactual_ensemble",
  "description": "Initialize on the actual 2020 network and evolve a 300-member no-rewiring ensemble forward to 2028 on actual and projected GDPs, then measure corridor divergence against the actual network.",
  "inputs": {
    "n_runs":      { "type": "integer", "default": 300, "minimum": 1, "description": "Ensemble members. Changing this invalidates comparison with the printed figures." },
    "seed0":       { "type": "integer", "default": 1000, "description": "First member seed. Member k uses seed0 + k." },
    "max_workers": { "type": "integer", "default": 8, "minimum": 1, "description": "Process-pool width. Affects wall time only, never results." },
    "corridors":   { "type": "array", "items": { "type": "string", "pattern": "^[A-Z]{3}-[A-Z]{3}$" }, "default": "the nine printed corridors", "description": "Undirected ISO3 pairs to report, order-insensitive." }
  },
  "returns": {
    "corridors": { "type": "array", "items": { "type": "object", "properties": {
        "corridor":   { "type": "string",  "description": "ISO3 pair, alphabetically ordered." },
        "year":       { "type": "integer" },
        "cf_p50":     { "type": "number",  "description": "Ensemble median pair weight, model units on the kappa scale." },
        "cf_p5":      { "type": "number" },
        "cf_p95":     { "type": "number" },
        "actual":     { "type": ["number","null"], "description": "Actual pair weight where BACI coverage exists, otherwise null." },
        "raw_pctile": { "type": "number", "minimum": 0, "maximum": 1, "description": "NOT A P-VALUE. See section 7, guardrail G2." } } } },
    "ensemble_csv":  { "type": "string" },
    "corridors_csv": { "type": "string" },
    "duration_s":    { "type": "number" }
  },
  "guardrail": "Any surface that renders raw_pctile must render the empirical-null percentile from run_empirical_null alongside it."
}
```

### 4.5 `run_attack_percolation` (capability C5)

```jsonc
{
  "name": "run_attack_percolation",
  "description": "Percolate the actual undirected weighted 2024 trade network under strength-targeted, betweenness-targeted, and random node removal, and report surviving connected trade weight.",
  "inputs": {
    "strategies":  { "type": "array", "items": { "type": "string", "enum": ["targeted_strength","targeted_betweenness","random"] }, "default": "all three" },
    "fractions":   { "type": "array", "items": { "type": "number", "minimum": 0, "maximum": 1 }, "default": "0.00 to 0.40 in steps of 0.02", "description": "Node-removal fractions to evaluate." },
    "n_random":    { "type": "integer", "default": 100, "description": "Random-order replicates used to form the 5th to 95th percentile band." },
    "seed0":       { "type": "integer", "default": 7000 }
  },
  "returns": {
    "curves": { "type": "array", "items": { "type": "object", "properties": {
        "strategy":         { "type": "string" },
        "metric":           { "type": "string", "enum": ["lcc_node_share","lcc_share_of_surviving_weight","lcc_share_of_original_weight"] },
        "fraction_removed": { "type": "number", "description": "Dimensionless share of nodes removed." },
        "value":            { "type": "number", "minimum": 0, "maximum": 1, "description": "Dimensionless share. For random this is the median across replicates." },
        "p5":               { "type": ["number","null"] },
        "p95":              { "type": ["number","null"] } } } },
    "partition_point": { "type": "object", "additionalProperties": { "type": ["number","null"] }, "description": "Per strategy, the first removal fraction where lcc_share_of_original_weight falls below 0.5." },
    "csv_path":        { "type": "string" },
    "duration_s":      { "type": "number" }
  }
}
```

### 4.6 `run_uniformity_placebo` (capability C7)

```jsonc
{
  "name": "run_uniformity_placebo",
  "description": "Test whether the no-rewiring ensemble is a calibrated null by pushing every comparable untreated country pair through it and testing the resulting percentiles for uniformity. Runs two 300-member ensembles.",
  "inputs": {
    "windows":     { "type": "array", "items": { "type": "string", "enum": ["2020_2024","2017_2019"] }, "default": "both", "description": "2020_2024 is the printed window; 2017_2019 is the pre-COVID backtest." },
    "n_runs":      { "type": "integer", "default": 300 },
    "max_workers": { "type": "integer", "default": 8 }
  },
  "returns": {
    "results": { "type": "object", "additionalProperties": { "type": "object", "properties": {
        "n_dyads":        { "type": "integer", "description": "Comparable country pairs, approximately 2,653 for the printed window." },
        "ks":             { "type": "number", "description": "Kolmogorov-Smirnov distance to U[0,1]. Dimensionless." },
        "ks_p":           { "type": "number" },
        "frac_below_p5":  { "type": "number", "description": "Share below the ensemble 5th percentile. 0.05 expected under a calibrated null." },
        "frac_above_p95": { "type": "number" },
        "named":          { "type": "object", "additionalProperties": { "type": "number" }, "description": "Raw ensemble percentile per named corridor, in [0,1]." } } } },
    "calibrated": { "type": "boolean", "description": "False for every shipped window. The instrument fails its own test by design of the test, not by accident." },
    "json_path":  { "type": "string" },
    "duration_s": { "type": "number" }
  },
  "guardrail": "A caller that receives calibrated=false must route corridor questions through run_empirical_null before answering."
}
```

### 4.7 `run_empirical_null` (capability C8)

```jsonc
{
  "name": "run_empirical_null",
  "description": "Rebuild the null from the cross-section of deviations rather than from the generator's own bands, following Efron. Returns the corrected corridor readings and the over-dispersion factor that quantifies how over-confident the raw bands were.",
  "inputs": {
    "windows":   { "type": "array", "items": { "type": "string", "enum": ["2020_2024","2017_2019"] }, "default": "both" },
    "corridors": { "type": "array", "items": { "type": "string", "pattern": "^[A-Z]{3}-[A-Z]{3}$" }, "default": "the six named corridors" },
    "n_runs":    { "type": "integer", "default": 300 }
  },
  "returns": {
    "windows": { "type": "object", "additionalProperties": { "type": "object", "properties": {
        "n":               { "type": "integer", "description": "Comparable country pairs." },
        "sd_cross":        { "type": "number", "description": "Cross-sectional standard deviation of r, in dex, where one dex is a factor of ten." },
        "sd_model":        { "type": "number", "description": "Median within-pair model standard deviation, in dex." },
        "over_dispersion": { "type": "number", "description": "sd_cross divided by sd_model. Approximately 4.1 for the printed window and 10.7 for the pre-period." },
        "named": { "type": "object", "additionalProperties": { "type": "object", "properties": {
            "dev_dex":           { "type": "number", "description": "r = log10(actual / ensemble median)." },
            "ratio_vs_median":   { "type": "number", "description": "10 raised to dev_dex. Dimensionless multiple of the benchmark." },
            "empirical_pctile":  { "type": "number", "minimum": 0, "maximum": 1, "description": "THE QUOTABLE FIGURE. Rank of this corridor's deviation among all comparable country pairs." } } } } } } },
    "json_path":  { "type": "string" },
    "duration_s": { "type": "number" }
  }
}
```

### 4.8 `export_calibration` (capability C9)

```jsonc
{
  "name": "export_calibration",
  "description": "Re-run the printed 2020 to 2024 ensemble on the paper's seeds and export the two calibration histograms plus named-corridor markers as a standalone calibration record. Adds no new inference.",
  "inputs": {
    "pct_bins": { "type": "integer", "default": 20, "description": "Bin count for the raw-percentile histogram, which is flat if and only if the null is calibrated." },
    "r_bins":   { "type": "integer", "default": 40, "description": "Bin count for the deviation histogram." },
    "n_runs":   { "type": "integer", "default": 300 },
    "seed":     { "type": "integer", "default": 1000, "description": "Must match run_uniformity_placebo for the printed numbers to agree." }
  },
  "returns": {
    "n":            { "type": "integer" },
    "pct_hist":     { "type": "object", "properties": { "counts": {"type":"array","items":{"type":"integer"}}, "edges": {"type":"array","items":{"type":"number"}}, "expected": {"type":"number","description":"Per-bin count under uniformity."} } },
    "r_hist":       { "type": "object", "properties": { "counts": {"type":"array","items":{"type":"integer"}}, "edges": {"type":"array","items":{"type":"number","description":"Deviation in dex."}} } },
    "over":         { "type": "number" },
    "ks":           { "type": "number" },
    "json_path":    { "type": "string" },
    "duration_s":   { "type": "number" }
  }
}
```

### 4.10 Read-Only Accessors

Three further tools serve questions that need an answer rather than a run. Since each reads
committed JSON or CSV and returns in milliseconds, so an implementer should prefer them over
re-running an ensemble whenever the shipped seeds suffice.

| Tool | Inputs | Returns |
|---|---|---|
| `read_corridor_reading` | `corridor` (string, `^[A-Z]{3}-[A-Z]{3}$`), `window` (enum `2020_2024`, `2017_2019`) | `ratio_vs_median` (number), `empirical_pctile` (number in [0,1]), `raw_pctile` (number, flagged not-a-p-value), `over_dispersion` (number), `interpretation` (string, the sanctioned sentence) |
| `read_slate_forecast` | `id` (string, `^(A[1-3]\|B[4-5]\|C[6-9]\|D10)$`), optional | `id`, `group`, `probability` (integer 0 to 100), `claim` (string), `resolver` (string), `threshold` (number), `unit` (string), `current` (number or null), `as_of` (string) |
| `read_attack_curve` | `strategy` (enum), `metric` (enum), `fraction_removed` (number) | `value` (number in [0,1]), `p5`, `p95`, `partition_point` (number or null) |

*Source: Author (2026).*

---

## 5. Determinism and Reproducibility

Which reruns must reproduce, and which need not, is stated exactly here, so an agent comparing two
runs can tell a real change from expected variation. The guarantee is narrow.
Every script fixes its seeds at module scope, and no script reads the system clock or an environment
variable into a result.

**Fixed seeds by script.** `40_counterfactual.py` uses base 1000 across 300 members. `41_attack.py`
uses base 7000 across 100 random-order replicates. `70_rf_rigor.py` uses 42 for every random forest
at 400 trees. `71_placebo.py` uses 1000 for the printed window and 5000 for the pre-period.
`72_empirical_null.py` and `73_calib_export.py` reuse those same two bases precisely so their
outputs agree with the placebo's, which is the property that lets every surface print one set of
numbers. `validate_completnet.py` defaults to base 42 and increments per iteration.

**Worker count does not affect results.** The process pools set `max_workers=8`. Each
member is seeded independently by rank rather than by scheduling order, so a run on 2 workers and a
run on 32 workers return identical arrays. Only wall time moves.

**The expensive scripts.** `40_counterfactual.py` runs one 300-member ensemble across eight years
and takes roughly 2 to 4 minutes. `71_placebo.py` and `72_empirical_null.py` each run two 300-member
ensembles and take roughly 6 to 10 minutes. `73_calib_export.py` runs one and takes roughly 3 to 5
minutes. `20_multigraph.py`, `70_rf_rigor.py`, and `validate_completnet.py` are
single-digit-minute jobs.

**Byte-stability.** `20_multigraph.py` fixes ordering and rounding so its CSVs are byte-stable
across reruns. A non-empty diff therefore signals a moved input rather than nondeterminism.

One caveat bounds all of the above. NumPy does not formally guarantee the `Generator` bit stream
across feature releases; NEP 19 reserves the right to change it, and only the legacy `RandomState`
carries a stream-compatibility guarantee. We measured it rather than trusting it: the `gamma`,
`random`, and `choice` streams this port depends on are byte-identical across NumPy 1.26.4 through
2.4.6, the full range `requirements.txt` admits, and the GDP matrix is identical across pandas 2.1.4
through 2.3.3. A change to `scikit-learn`'s tree-building internals would still move
`70_rf_rigor.py` output without any seed changing, which is why its ceiling is pinned. Pinning the
full environment rather than the top-level packages remains the next step here.

---

## 6. Data Contracts

This section lets an agent parse every shipped file without opening it first.
All CSVs carry one or more leading comment lines beginning with `#`, which must be
skipped, and every reader in the repository passes `comment="#"` for that reason.

### 6.1 `data/processed/wtw_agg_2017_2024.csv` (NOT SHIPPED, produced by C1)

| Column | Dtype | Unit | Notes |
|---|---|---|---|
| `year` | int64 | calendar year | 2017 through 2024 |
| `exporter_iso3` | object | ISO 3166-1 alpha-3 | BACI code 490, "Other Asia, nes", is recoded to TWN |
| `importer_iso3` | object | ISO 3166-1 alpha-3 | same recode |
| `value_kusd` | float64 | thousands of current USD | BACI's native `v` unit. USD equals `value_kusd` times 1e3 |

### 6.2 `data/processed/counterfactual_corridors.csv`

| Column | Dtype | Unit | Notes |
|---|---|---|---|
| `corridor` | object | ISO3 pair | Alphabetically ordered, undirected, so `CHN-USA` carries both directions |
| `year` | int64 | calendar year | 2021 through 2028 |
| `kind` | object | categorical | `cf` for counterfactual ensemble, `act` for actual |
| `p50`, `p5`, `p95` | float64 | model units, kappa scale | Not USD. See guardrail G2 before differencing against real values |

### 6.3 `data/processed/attack_curves.csv`

| Column | Dtype | Unit | Notes |
|---|---|---|---|
| `strategy` | object | categorical | `targeted_strength`, `targeted_betweenness`, `random` |
| `metric` | object | categorical | Three metrics, defined in the file's own header comment |
| `fraction_removed` | float64 | dimensionless share | 0.00 to 0.40 in steps of 0.02 |
| `value` | float64 | dimensionless share in [0,1] | Median across replicates for `random` |
| `p5`, `p95` | float64 or null | dimensionless share | Populated for `random` only |

### 6.4 `data/processed/placebo_results.json`

Top-level keys are `A_2020_2024` and `B_2017_2019`. Each holds `label` (string), `y0` and `y1`
(int, calendar years), `n_dyads` (int), `ks` and `ks_p` (float, dimensionless), `mean` and `median`
(float in [0,1]), `frac_below_p5` and `frac_above_p95` (float in [0,1]), and `named` (object mapping
corridor string to raw percentile in [0,1]).

### 6.5 `data/processed/empirical_null.json`

Top-level keys are `main_2020_2024` and `pre_2017_2019`. Each holds `label`, `y0`, `y1`, `n` (int),
`sd_cross` and `sd_model` (float, dex), `over_dispersion` (float, dimensionless ratio), and `named`,
an object mapping corridor string to `{dev_dex, ratio_vs_median, empirical_pctile}`. **The quotable
field is `empirical_pctile`.**

### 6.6 `data/processed/calib_export.json`

Holds `n` (int), `pct_hist` (`counts` of 20 ints, `edges` of 21 floats, `expected` float),
`r_hist` (`counts` of 40 ints, `edges` of 41 floats in dex), `sd_cross`, `sd_model_med`, `over`,
`ks`, `below_p5`, `above_p95` (all float), and `named`, mapping corridor to `{raw_pct, r, ratio,
emp_pct, sd_model}`.

### 6.7 `data/processed/port_validation.csv`

One row per year from 1996 to 2020 with columns `year` (int64) plus `E`, `density`, `mu_deg`,
`sd_deg`, `mu_sp`, `sd_sp`, `mu_cc`, `sd_cc`, and `kcore`, all float64 and all dimensionless graph
statistics averaged over the configured iterations.

### 6.8 `data/processed/multigraph/*_edges.csv`

One file per sector layer, holding the full directed edge list as exporter to importer with weights
in thousands of USD. Edges below 1 kUSD are omitted before construction, and weighted directed
betweenness uses distance equal to 1 divided by ln(1 plus `v_kusd`), so larger flows sit on shorter
paths.

## 7. Guardrails

Four ways exist for an agent to mislead a reader while running everything correctly. They are named
here. These are not style preferences. Each corresponds to a
specific defect the project caught in itself.

**G1. Never redistribute raw BACI.** The CEPII licence does not permit redistribution of the raw HS6
archive, and this repository therefore ships neither `baci_2024_hs6.parquet` nor
`baci_country_codes.csv` nor the aggregated panel derived directly from them. Given that the
restriction sits on the raw distribution rather than on analysis, an agent may download BACI from
cepii.fr into a local working directory, and it may publish derived statistics, figures, and
aggregate tables. It must not re-serve, mirror, upload, or attach the raw files or the full
bilateral panel. When a caller asks for the panel, the correct response is the download instruction
plus capability C1, never the file.

**G2. Never present a raw ensemble percentile as a p-value.** The counterfactual bands failed their
own uniformity placebo. Approximately 28.3% of roughly 2,653 untreated country pairs land below the
ensemble's 5th percentile and approximately 27.5% above its 95th, against 5% expected at each tail,
with a KS distance to uniform of approximately 0.239. The generator's within-pair dispersion is
approximately 0.104 dex against a real cross-section of approximately 0.421 dex, so the bands run
approximately 4.1x too tight, and roughly 10.7x too tight in the 2017 to 2019 pre-period. Any
statement of the form "this corridor sits at the Nth percentile of the ensemble" is therefore
inadmissible on its own. The admissible statement quotes `empirical_pctile` from
`empirical_null.json` and names it as a rank among all comparable country pairs.

**G3. Never alter a printed forecast probability without recording the rationale.** The ten
probabilities were set by the author in a verification pass held separate from model construction,
and at least one was set against the model's own posterior on stated judgment. An
agent may compute an updated probability, present it as a proposal, and show its drivers.
Editing the value in `notes/LOCKED-SLATE-v5.md` or in any downstream
surface without a dated written rationale alongside it breaks the audit chain that makes the slate
scoreable.

**G4. The slate IDs are stable and must not be renumbered.** A1, A2, A3, B4, B5, C6, C7, C8, C9, and
D10 are frozen at v5.0. Exactly one renumbering has ever been performed, documented in
`notes/LOCKED-SLATE-v5.md`, and it will not happen again. Adding a forecast means appending a new ID
rather than reflowing the sequence, and retiring one means marking it retired in place. An agent
that renumbers silently makes every prior citation of a forecast ambiguous.

G2 is the one an agent is most likely to violate accidentally, because
`counterfactual_corridors.csv` and `40_counterfactual.py` both return the raw percentile without a
warning attached to the number itself. Attaching that warning at the tool boundary rather than
relying on documentation is the right fix, and section 4.4 specifies it as a response-envelope
guardrail for exactly that reason.

---

## 8. Worked Example

**Question posed to the agent: "Is the China-US corridor unusually suppressed?"**

The naive path answers from `counterfactual_corridors.csv`, reports the raw percentile of roughly
12, and calls the corridor extreme. That answer is wrong, and it is wrong in the specific
way guardrail G2 exists to prevent. The correct sequence follows.

**Step 1. Establish whether the null is calibrated before quoting anything from it.** Read
`data/processed/placebo_results.json`, or call `run_uniformity_placebo`. Therefore the printed
window returns a KS distance of approximately 0.239 against U[0,1] across roughly 2,653 comparable
country pairs, with approximately 28.3% below the 5th percentile and approximately 27.5% above the 95th. The
null is therefore not calibrated, and no raw percentile from the ensemble is a p-value.

**Step 2. Quantify how badly.** Read `over_dispersion` from `data/processed/empirical_null.json`, or
call `run_empirical_null`. The printed window returns approximately 4.1x, being a cross-sectional
deviation of approximately 0.421 dex against a median within-pair model dispersion of approximately
0.104 dex. A raw percentile of 12 is therefore ordinary rather than extreme, since roughly a quarter of all
untreated country pairs sit below 5.

**Step 3. Read the corrected figure, not the raw one.** From this same file, the `CHN-USA` entry
returns `ratio_vs_median` of approximately 0.86 and `empirical_pctile` of approximately 0.344. The
corridor carries roughly 86% of its GDP-implied benchmark median, which ranks at roughly the 34th
percentile of all comparable country pairs by deviation.

**Step 4. Bound the reading against the pre-period.** The `pre_2017_2019` block puts the same
corridor at roughly the 21.8th empirical percentile in 2019 against roughly the 34.4th in 2024.
Most of the suppression therefore predates the ensemble's 2020 start line, since initializing on
2020 bakes the 2018 to 2019 trade-war suppression into the initial condition. The ensemble measures
incremental rewiring since 2020, not cumulative rewiring since the first tariffs.

**Step 5. Lead with the wider baseline, then the refinement.** The descriptive gravity fit, a
per-year OLS on directed flows, puts China-US at approximately 0.35x its GDP-implied weight. That is
the total displacement. The ensemble reading of approximately 0.86x is the increment since 2020, and
it is smaller because initializing on 2020 banks the earlier suppression into the starting condition.
State the relationship in that order. Two numbers with an explicit relationship read as precision;
two numbers side by side read as hedging, and the paper's own review caught them fused into one
sentence.

**Step 6. Answer.** The sanctioned form is this. *The China-US corridor is suppressed relative to
its GDP-implied benchmark, carrying approximately 0.86x the ensemble's median weight and ranking at
roughly the 34th percentile of approximately 2,653 comparable country pairs. The direction is clear and the
magnitude is ordinary-large rather than extreme. The generator's own percentile bands would have
called it extreme, at roughly the 12th percentile; those bands run approximately 4.1x too tight and
failed a uniformity placebo, so the empirical-null rank is the figure that holds. A pre-period
backtest places most of the suppression before 2020.*

A note on what this example cannot deliver. The empirical null buys honesty at the cost of
power, so it cannot distinguish a targeted shock from an ordinary large one and reports rank rather
than significance. Fitting a pair-level volatility model, which would restore a calibrated
per-corridor null without discarding the generator, is the natural next piece of work.
