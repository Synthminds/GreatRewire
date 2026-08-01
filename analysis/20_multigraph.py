#!/usr/bin/env python3
"""
This script prices the mercantilist grab for chokepoints on the world
trade network. To achieve this objective we build five strategic-sector layers from BACI 2024
HS6 flows, place them alongside the all-products 2024 aggregate graph, and emit the chokepoint
and concentration tables that name the chokepoints rather than gesture at them.

20_multigraph.py -- B1 strategic-sector dependency multigraph (Appendix B1 + Exhibit X1 inputs).

Inputs (produced by analysis/10_baci_aggregate.py):
  data/processed/baci_2024_hs6.parquet     t,i,j,k,v,q; v = THOUSANDS of USD; k = HS6 string
  data/processed/baci_country_codes.csv    BACI code -> iso3_recode (Taiwan 490 -> TWN)
  data/processed/wtw_agg_2017_2024.csv     all-products bilateral totals per year

Outputs (all under data/processed/multigraph/ unless noted; provenance headers;
fixed ordering + fixed rounding so reruns are byte-stable):
  {layer}_edges.csv            full directed edge list per layer (exporter->importer, kUSD)
  chokepoint_table.csv         per layer: top-10 by export share / betweenness / eigenvector
  focus_country_ranks.csv      TWN/CHN/USA/KOR/JPN/NLD ranks in every layer, all metrics
  product_concentration.csv    per layer x HS6: export-origin HHI, dominant exporter, value
  agg_2024_ranks.csv           all-products 2024 strength + betweenness ranks (context)
  x1_nodes_edges.json          Exhibit X1 input: top ~30 strategic nodes + top-15 edges/layer

Conventions (stated once, employed everywhere):
  * Weights are BACI 'v' in THOUSANDS of current USD (kUSD). USD = kUSD * 1e3.
  * De minimis: we omit layer edges below 1 kUSD (USD 1,000) before graph
    construction and edge-list output, since dust flows carry no analytic content.
  * Betweenness: weighted directed betweenness with edge distance
    dist = 1 / ln(1 + v_kusd). Bigger flows therefore yield shorter distances, so
    shortest paths preferentially traverse high-volume trade corridors.
  * Eigenvector centrality: we compute it on the UNDIRECTED weighted projection
    (edge weight = v(u->w) + v(w->u)), power iteration, tol=1e-10.
  * HHI: sum of squared shares scaled to 0..10,000 (DOJ/FTC convention).
    Anything above 2,500 counts as highly concentrated.
  * Layer membership is by HS6 prefix match (k is a 6-char string with leading
    zeros; 4/5/6-char prefixes). A code may sit in two layers, as lithium
    hydroxide 282520 is both a critical-mineral and a battery precursor. This is
    a multigraph by design: the layers are analytic apertures, not a partition.

Source:  CEPII BACI HS17 V202601 (year 2024), Etalab 2.0 license.
Run:     python3 analysis/20_multigraph.py
"""

import json
import os

import networkx as nx
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(PROC, "multigraph")

VERSION = "V202601"
HS = "HS17"
YEAR = 2024
SCRIPT_DATE = "2026-07-30"          # the data-pull vintage, not a run timestamp; reruns stay byte-stable

DE_MINIMIS_KUSD = 1.0               # we omit layer edges below USD 1,000
PRODUCT_FLOOR_KUSD = 5.0e5          # named-chokepoint candidates need >= USD 500M in world trade
TOP_N = 10                          # chokepoint table depth
X1_TOP_NODES = 30                   # Exhibit X1 node count
X1_TOP_EDGES = 15                   # Exhibit X1 edges per layer
FOCUS = ["TWN", "CHN", "USA", "KOR", "JPN", "NLD"]

# ---------------------------------------------------------------------------
# Strategic-sector layers: HS6 prefix -> one-line rationale. We adopt CRS/CSIS-style
# groupings, and each line carries both the code choice's justification and its label.
# ---------------------------------------------------------------------------
LAYERS = {
    "semiconductors": {
        "8541": "Semiconductor devices: diodes, transistors, LEDs, photovoltaic cells (discrete semis)",
        "8542": "Electronic integrated circuits: processors, memory, amplifiers (the core chip trade)",
        "8486": "Semiconductor/flat-panel manufacturing equipment incl. lithography (EUV sits in 848620)",
    },
    "critical_minerals": {
        "2805": "Alkali/alkaline-earth + rare-earth metals, Sc, Y, Hg (280530 = rare-earth metals proper)",
        "2846": "Compounds of rare-earth metals, yttrium, scandium (REE oxides/salts, magnet feedstock)",
        "2844": "Radioactive elements incl. natural + enriched uranium (fuel-cycle dependency)",
        "8505": "Electromagnets + permanent magnets (850511 = metal permanent magnets, i.e. NdFeB/SmCo)",
        "8112": "Be, Cr, Ge, V, Ga, Hf, In, Nb, Re, Tl wrought/unwrought (Ga/Ge under CHN export controls)",
        "28046": "Silicon: 280461 (>=99.99% pure, polysilicon for wafers) + 280469 (metallurgical Si)",
        "2504": "Natural graphite (anode feedstock; CHN export permits since Dec 2023)",
        "3801": "Artificial graphite + graphite preparations (battery-anode material)",
        "282520": "Lithium oxide and hydroxide (battery-grade lithium chain)",
        "282530": "Vanadium oxides and hydroxides (USGS-critical V chain)",
        "282540": "Nickel oxides and hydroxides (cathode chain, USGS-critical Ni)",
        "282560": "Germanium oxides + zirconium dioxide (Ge under CHN export controls since Aug 2023)",
        "282580": "Antimony oxides (Sb under CHN export controls since Sep 2024)",
        "284161": "Potassium permanganate (manganese chain)",
        "284169": "Manganites, manganates, other permanganates (manganese chain)",
        "284180": "Tungstates (W under CHN export controls Feb 2025)",
        "284190": "Other oxometallic/peroxometallic salts incl. vanadates, niobates",
    },
    "batteries": {
        "8507": "Electric accumulators: cells, packs, parts (850760 = lithium-ion, the dominant line)",
        "282520": "Lithium oxide and hydroxide (precursor; shared with critical_minerals by design)",
        "283691": "Lithium carbonates (precursor salt for cathode manufacture)",
    },
    # Standard API basket: organic-chemistry chapters HS 2933-2942 (heterocycles,
    # sulfonamides, vitamins, hormones, glycosides, alkaloids, sugars, antibiotics).
    # We follow the CRS/Avalere convention for active pharmaceutical ingredients.
    "pharma_apis": {
        "2933": "Heterocyclic compounds, nitrogen hetero-atoms (core API scaffolds)",
        "2934": "Nucleic acids and other heterocyclic compounds",
        "2935": "Sulfonamides",
        "2936": "Provitamins and vitamins",
        "2937": "Hormones incl. steroids and insulin",
        "2938": "Glycosides",
        "2939": "Alkaloids (opiates, caffeine, ephedrines, etc.)",
        "2940": "Chemically pure sugars, sugar ethers/esters",
        "2941": "Antibiotics (penicillins, cephalosporins, macrolides, etc.)",
        "2942": "Other organic compounds",
    },
    "aerospace": {
        "8802": "Aircraft and spacecraft: airplanes, helicopters, satellites, launch vehicles",
        "8411": "Turbojets, turboprops, other gas turbines + parts (the aeroengine trade)",
    },
}
LAYER_ORDER = list(LAYERS.keys())

PROVENANCE = (
    "# source: CEPII BACI {hs} {ver}, year {yr} (via data/processed/baci_2024_hs6.parquet)\n"
    "# pulled: {d}\n"
    "# license: Etalab 2.0\n"
    "# script: analysis/20_multigraph.py\n"
    "# unit: *_kusd values are THOUSANDS of current USD (BACI native 'v'); USD = kusd * 1e3\n"
    "# note: Taiwan = BACI code 490 'Other Asia, nes', recoded to TWN (iso3_recode)\n"
    "# note: de minimis {dm} kUSD on layer edges; HHI on 0..10,000 scale;\n"
    "#       betweenness distance = 1/ln(1+v_kusd); eigenvector on undirected projection\n"
).format(hs=HS, ver=VERSION, yr=YEAR, d=SCRIPT_DATE, dm=DE_MINIMIS_KUSD)


def write_csv(path, df, extra_notes=()):
    """Write df beneath the provenance header block. The caller fixes row order."""
    with open(path, "w", newline="") as fh:
        fh.write(PROVENANCE)
        for line in extra_notes:
            fh.write(f"# {line}\n")
        df.to_csv(fh, index=False)
    print(f"wrote {os.path.relpath(path, ROOT)} ({len(df):,} rows)")


def hhi_0_10000(values):
    """Herfindahl-Hirschman index of a value vector, 0..10,000 scale."""
    total = float(values.sum())
    if total <= 0:
        return np.nan
    shares = np.asarray(values, dtype=float) / total
    return round(float((shares ** 2).sum()) * 10000.0, 1)


def layer_code_sets(unique_codes):
    """Resolve each layer's HS6 prefix list against the codes present in the data."""
    out = {}
    for layer, prefixes in LAYERS.items():
        pfx = tuple(sorted(prefixes))
        codes = sorted(c for c in unique_codes if c.startswith(pfx))
        if not codes:
            raise RuntimeError(f"layer {layer!r}: no HS6 codes matched -- check prefix strings")
        out[layer] = codes
    return out


def code_label(code):
    """Yield the human label for an HS6 code: the rationale line of its longest matching prefix."""
    best, best_len = "", -1
    for prefixes in LAYERS.values():
        for p, label in prefixes.items():
            if code.startswith(p) and len(p) > best_len:
                best, best_len = label, len(p)
    return best


def build_digraph(edges):
    """Build the directed weighted graph from (src,dst,value_kusd) rows in deterministic order."""
    g = nx.DiGraph()
    g.add_nodes_from(sorted(set(edges["src"]) | set(edges["dst"])))
    for row in edges.sort_values(["src", "dst"]).itertuples(index=False):
        g.add_edge(row.src, row.dst, weight=row.value_kusd,
                   dist=1.0 / np.log1p(row.value_kusd))
    return g


def undirected_projection(edges):
    """Build the undirected graph, weight = flow(u->v) + flow(v->u), in deterministic order."""
    und = {}
    for row in edges.itertuples(index=False):
        key = (row.src, row.dst) if row.src < row.dst else (row.dst, row.src)
        und[key] = und.get(key, 0.0) + row.value_kusd
    g = nx.Graph()
    g.add_nodes_from(sorted(set(edges["src"]) | set(edges["dst"])))
    for (u, v) in sorted(und):
        g.add_edge(u, v, weight=und[(u, v)])
    return g


def centrality_frame(edges):
    """Yield betweenness (directed, dist=1/ln(1+w)) and eigenvector (undirected) per country."""
    dg = build_digraph(edges)
    btw = nx.betweenness_centrality(dg, weight="dist", normalized=True)
    ug = undirected_projection(edges)
    try:
        eig = nx.eigenvector_centrality(ug, weight="weight", max_iter=5000, tol=1e-10)
    except nx.PowerIterationFailedConvergence:            # pragma: no cover
        eig = nx.eigenvector_centrality_numpy(ug, weight="weight")
    df = pd.DataFrame(
        {"iso3": sorted(dg.nodes()),
         "betweenness": [round(btw[n], 6) for n in sorted(dg.nodes())],
         "eigenvector": [round(eig.get(n, 0.0), 6) for n in sorted(dg.nodes())]}
    )
    return df


def rank_of(series_desc):
    """Competition rank, 1 = largest. Ties resolve deterministically through index order."""
    return series_desc.rank(ascending=False, method="min").astype(int)


def main():
    os.makedirs(OUT, exist_ok=True)

    # ---- country map ------------------------------------------------------
    cc = pd.read_csv(os.path.join(PROC, "baci_country_codes.csv"), comment="#")
    iso3 = cc.set_index("country_code")["iso3_recode"].to_dict()

    # ---- BACI 2024 HS6 flows ---------------------------------------------
    baci = pd.read_parquet(os.path.join(PROC, "baci_2024_hs6.parquet"),
                           columns=["i", "j", "k", "v"])
    assert (baci["k"].str.len() == 6).all(), "HS6 keys must be 6-char strings"
    codes_by_layer = layer_code_sets(baci["k"].unique())

    # ---- all-products 2024 aggregate graph (context) ----------------------
    wtw = pd.read_csv(os.path.join(PROC, "wtw_agg_2017_2024.csv"), comment="#")
    agg = (wtw[wtw["year"] == YEAR]
           .rename(columns={"exporter_iso3": "src", "importer_iso3": "dst",
                            "value_kusd": "value_kusd"})
           [["src", "dst", "value_kusd"]]
           .query("src != dst")
           .reset_index(drop=True))
    out_s = agg.groupby("src")["value_kusd"].sum()
    in_s = agg.groupby("dst")["value_kusd"].sum()
    strength = (out_s.add(in_s, fill_value=0.0)).rename("agg_strength_kusd")
    agg_cent = centrality_frame(agg)
    agg_tab = (agg_cent.merge(strength.reset_index().rename(columns={"index": "iso3", "src": "iso3"}),
                              on="iso3", how="left")
               .fillna({"agg_strength_kusd": 0.0}))
    agg_tab["agg_strength_kusd"] = agg_tab["agg_strength_kusd"].round(3)
    agg_tab["agg_strength_rank"] = rank_of(agg_tab["agg_strength_kusd"])
    agg_tab["agg_betweenness_rank"] = rank_of(agg_tab["betweenness"])
    agg_tab = (agg_tab.rename(columns={"betweenness": "agg_betweenness",
                                       "eigenvector": "agg_eigenvector"})
               .sort_values(["agg_strength_rank", "iso3"]).reset_index(drop=True))
    write_csv(os.path.join(OUT, "agg_2024_ranks.csv"),
              agg_tab[["iso3", "agg_strength_kusd", "agg_strength_rank",
                       "agg_betweenness", "agg_betweenness_rank", "agg_eigenvector"]],
              ["all-products 2024 graph from wtw_agg_2017_2024.csv; strength = exports + imports"])
    agg_ctx = agg_tab.set_index("iso3")[["agg_strength_rank", "agg_betweenness_rank"]]

    # ---- per-layer build ---------------------------------------------------
    choke_rows, focus_rows, product_rows = [], [], []
    layer_strength = {}                 # iso3 -> {layer: strength kUSD}
    x1_edges = []

    for layer in LAYER_ORDER:
        codes = codes_by_layer[layer]
        sub = baci[baci["k"].isin(codes)].copy()
        sub["src"] = sub["i"].map(iso3)
        sub["dst"] = sub["j"].map(iso3)
        assert not sub["src"].isna().any() and not sub["dst"].isna().any(), \
            f"{layer}: unmapped BACI country codes"

        # -- product-level concentration, computed pre-aggregation with no de minimis ----
        pk = sub.groupby(["k", "src"], sort=True)["v"].sum().reset_index()
        for k_code, grp in pk.groupby("k", sort=True):
            grp = grp.sort_values(["v", "src"], ascending=[False, True])
            world = float(grp["v"].sum())
            top1, top2 = grp.iloc[0], (grp.iloc[1] if len(grp) > 1 else None)
            product_rows.append({
                "layer": layer, "hs6": k_code, "label": code_label(k_code),
                "world_kusd": round(world, 3),
                "export_hhi": hhi_0_10000(grp["v"]),
                "top_exporter": top1["src"],
                "top_share_pct": round(100.0 * top1["v"] / world, 2),
                "second_exporter": None if top2 is None else top2["src"],
                "second_share_pct": None if top2 is None else round(100.0 * top2["v"] / world, 2),
            })

        # -- dyadic edges: de minimis applied, ordering fixed for byte-stable reruns ----
        edges = (sub.groupby(["src", "dst"], sort=True)["v"].sum()
                 .reset_index().rename(columns={"v": "value_kusd"})
                 .query("src != dst and value_kusd >= @DE_MINIMIS_KUSD")
                 .reset_index(drop=True))
        edges["value_kusd"] = edges["value_kusd"].round(3)
        edges = edges.sort_values(["value_kusd", "src", "dst"],
                                  ascending=[False, True, True]).reset_index(drop=True)
        write_csv(os.path.join(OUT, f"{layer}_edges.csv"),
                  edges.rename(columns={"src": "exporter_iso3", "dst": "importer_iso3"}),
                  [f"layer = {layer}; HS6 codes ({len(codes)}): {','.join(codes)}"])

        # -- exporter shares + layer HHI -------------------------------------
        exp = edges.groupby("src")["value_kusd"].sum().sort_index()
        world_kusd = float(exp.sum())
        lhhi = hhi_0_10000(exp)
        shares = (exp / world_kusd * 100.0).round(4)
        exp_tab = pd.DataFrame({"iso3": exp.index, "export_kusd": exp.values.round(3),
                                "share_pct": shares.values})
        exp_tab["rank"] = rank_of(exp_tab["export_kusd"])
        exp_tab = exp_tab.sort_values(["rank", "iso3"]).reset_index(drop=True)

        # -- centralities ------------------------------------------------------
        cent = centrality_frame(edges)
        cent["btw_rank"] = rank_of(cent["betweenness"])
        cent["eig_rank"] = rank_of(cent["eigenvector"])

        # -- strengths for X1 --------------------------------------------------
        st = (edges.groupby("src")["value_kusd"].sum()
              .add(edges.groupby("dst")["value_kusd"].sum(), fill_value=0.0))
        for c, s in st.items():
            layer_strength.setdefault(c, {})[layer] = float(s)
        x1_edges.append(edges.head(X1_TOP_EDGES).assign(layer=layer))

        # -- chokepoint table rows: top-10 per metric, carrying all-products context ----
        def ctx(iso):
            if iso in agg_ctx.index:
                r = agg_ctx.loc[iso]
                return int(r["agg_strength_rank"]), int(r["agg_betweenness_rank"])
            return None, None

        for _, r in exp_tab.head(TOP_N).iterrows():
            a_s, a_b = ctx(r["iso3"])
            choke_rows.append({"layer": layer, "metric": "export_share", "rank": int(r["rank"]),
                               "iso3": r["iso3"], "value": r["share_pct"],
                               "unit": "pct_of_layer_exports",
                               "export_kusd": r["export_kusd"], "layer_export_hhi": lhhi,
                               "agg_strength_rank": a_s, "agg_betweenness_rank": a_b})
        for _, r in cent.sort_values(["btw_rank", "iso3"]).head(TOP_N).iterrows():
            a_s, a_b = ctx(r["iso3"])
            choke_rows.append({"layer": layer, "metric": "betweenness", "rank": int(r["btw_rank"]),
                               "iso3": r["iso3"], "value": r["betweenness"],
                               "unit": "normalized_betweenness",
                               "export_kusd": None, "layer_export_hhi": lhhi,
                               "agg_strength_rank": a_s, "agg_betweenness_rank": a_b})
        for _, r in cent.sort_values(["eig_rank", "iso3"]).head(TOP_N).iterrows():
            a_s, a_b = ctx(r["iso3"])
            choke_rows.append({"layer": layer, "metric": "eigenvector", "rank": int(r["eig_rank"]),
                               "iso3": r["iso3"], "value": r["eigenvector"],
                               "unit": "eigenvector_centrality",
                               "export_kusd": None, "layer_export_hhi": lhhi,
                               "agg_strength_rank": a_s, "agg_betweenness_rank": a_b})

        # -- focus-country flags ----------------------------------------------
        exp_ix = exp_tab.set_index("iso3")
        cent_ix = cent.set_index("iso3")
        for iso in FOCUS:
            a_s, a_b = ctx(iso)
            focus_rows.append({
                "layer": layer, "iso3": iso,
                "export_share_pct": float(exp_ix.loc[iso, "share_pct"]) if iso in exp_ix.index else 0.0,
                "export_rank": int(exp_ix.loc[iso, "rank"]) if iso in exp_ix.index else None,
                "betweenness_rank": int(cent_ix.loc[iso, "btw_rank"]) if iso in cent_ix.index else None,
                "eigenvector_rank": int(cent_ix.loc[iso, "eig_rank"]) if iso in cent_ix.index else None,
                "n_layer_countries": int(len(cent)),
                "agg_strength_rank": a_s, "agg_betweenness_rank": a_b,
            })

        print(f"  {layer}: {len(codes)} HS6 codes, {len(edges):,} edges, "
              f"{len(cent)} countries, world = {world_kusd/1e9:.3f} T USD, HHI = {lhhi:.0f}")

    # ---- we write the chokepoint, focus and product tables ------------------
    choke = pd.DataFrame(choke_rows)
    write_csv(os.path.join(OUT, "chokepoint_table.csv"), choke,
              ["top-10 per layer per metric; layer_export_hhi = HHI of layer export origin",
               "agg_* = rank in the all-products 2024 graph (context)"])

    focus = pd.DataFrame(focus_rows)
    write_csv(os.path.join(OUT, "focus_country_ranks.csv"), focus,
              [f"focus set = {','.join(FOCUS)}; None rank = country absent from layer"])

    products = (pd.DataFrame(product_rows)
                .sort_values(["layer", "export_hhi", "hs6"], ascending=[True, False, True])
                .reset_index(drop=True))
    products["layer"] = pd.Categorical(products["layer"], LAYER_ORDER, ordered=True)
    products = products.sort_values(["layer", "export_hhi", "hs6"],
                                    ascending=[True, False, True]).reset_index(drop=True)
    big = products["world_kusd"] >= PRODUCT_FLOOR_KUSD
    products["is_top5_concentrated"] = False
    for layer in LAYER_ORDER:
        m = (products["layer"] == layer) & big
        idx = products[m].nlargest(5, "export_hhi").index
        products.loc[idx, "is_top5_concentrated"] = True
    products["layer"] = products["layer"].astype(str)
    write_csv(os.path.join(OUT, "product_concentration.csv"), products,
              [f"is_top5_concentrated: 5 highest export-origin HHI codes per layer among "
               f"codes with world trade >= {PRODUCT_FLOOR_KUSD:.0f} kUSD (USD 500M floor)"])

    # ---- X1 exhibit input ----------------------------------------------------
    x1_edge_df = pd.concat(x1_edges, ignore_index=True)
    tot_strength = {c: round(sum(d.values()), 3) for c, d in layer_strength.items()}
    dom_layer = {c: max(LAYER_ORDER, key=lambda L: layer_strength[c].get(L, 0.0))
                 for c in layer_strength}
    top_nodes = sorted(tot_strength, key=lambda c: (-tot_strength[c], c))[:X1_TOP_NODES]
    endpoint_extra = sorted((set(x1_edge_df["src"]) | set(x1_edge_df["dst"])) - set(top_nodes))
    node_list = top_nodes + endpoint_extra
    x1 = {
        "meta": {
            "source": f"CEPII BACI {HS} {VERSION}, year {YEAR}",
            "script": "analysis/20_multigraph.py",
            "pulled": SCRIPT_DATE,
            "unit": "weight_kusd = thousands of current USD",
            "layers": LAYER_ORDER,
            "node_rule": f"top {X1_TOP_NODES} by combined strategic-layer strength "
                         f"(exports+imports summed over layers) + any extra edge endpoints",
            "edge_rule": f"top {X1_TOP_EDGES} edges per layer by value",
            "taiwan_note": "BACI code 490 'Other Asia, nes' recoded to TWN",
        },
        "nodes": [{"iso3": c,
                   "strategic_strength_kusd": tot_strength[c],
                   "dominant_layer": dom_layer[c]} for c in node_list],
        "edges": [{"src": r.src, "dst": r.dst, "layer": r.layer,
                   "weight_kusd": round(r.value_kusd, 3)}
                  for r in x1_edge_df.itertuples(index=False)],
    }
    x1_path = os.path.join(OUT, "x1_nodes_edges.json")
    with open(x1_path, "w") as fh:
        json.dump(x1, fh, indent=2)
        fh.write("\n")
    print(f"wrote {os.path.relpath(x1_path, ROOT)} "
          f"({len(x1['nodes'])} nodes, {len(x1['edges'])} edges)")

    # ---- sanity checks: we validate the build against three known facts -------
    semis_world = choke.query("layer == 'semiconductors' and metric == 'export_share'")
    semis_total = float(baci[baci["k"].isin(codes_by_layer["semiconductors"])]["v"].sum())
    assert 0.5e9 < semis_total < 2.5e9, f"semis world {semis_total/1e9:.2f}T out of O($1T) range"
    p = products.set_index(["layer", "hs6"])
    mag = products[(products["layer"] == "critical_minerals") &
                   (products["hs6"].str.startswith("8505"))]
    mag_top = (baci[baci["k"].str.startswith("8505")].assign(src=lambda d: d["i"].map(iso3))
               .groupby("src")["v"].sum().idxmax())
    assert mag_top == "CHN", f"8505 magnets top exporter {mag_top} != CHN -- check layer build"
    ics = (baci[baci["k"].str.startswith("8542")].assign(src=lambda d: d["i"].map(iso3))
           .groupby("src")["v"].sum().nlargest(2).index.tolist())
    assert "TWN" in ics, f"TWN not in top-2 IC (8542) exporters {ics} -- check TWN recode"
    print(f"sanity OK: semis world = {semis_total/1e9:.3f}T USD; "
          f"8505 top exporter = {mag_top}; top-2 IC exporters = {ics}")

    # ---- headline: the five most concentrated big products --------------------
    head = (products[products["is_top5_concentrated"]]
            .nlargest(5, "export_hhi")[["layer", "hs6", "top_exporter",
                                        "top_share_pct", "export_hhi", "world_kusd"]])
    print("\nTop-5 named chokepoints (HHI, >=$500M world trade):")
    for r in head.itertuples(index=False):
        print(f"  {r.hs6} [{r.layer}] {r.top_exporter} {r.top_share_pct:.1f}% "
              f"HHI={r.export_hhi:.0f} world=${r.world_kusd/1e6:.2f}B")
    print("DONE")


if __name__ == "__main__":
    main()
