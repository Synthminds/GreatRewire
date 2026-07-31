#!/usr/bin/env python3
"""Our fourth research objective seeks to establish how much trade value strength-targeted
removal strands against what random failure costs. To achieve this objective we percolate the
actual 2024 network under three removal strategies and read the gap between them as the
fragility measure. The topology holds and then the value structure partitions, which is the
finding, and the targeted-versus-random gap is what prices it.

Conventions: we build the undirected weighted 2024 graph from BACI aggregates, so a pair weight
carries flows in both directions. We employ three node-removal strategies: strength-targeted,
betweenness-targeted (distance 1/ln(1+w)), and random across 100 seeds with a 5-95% band. The
headline metric is the surviving-LCC weight share of ORIGINAL total weight, and we define the
partition point as the first removal fraction where that share falls below 0.5.

Of note, node removal here is an abstraction. A state does not delete a country from the
network, it re-prices a subset of that country's edges, so the curves bound the damage rather
than forecast it. Percolating on edge subsets rather than whole nodes is a natural extension.

Output: data/processed/attack_curves.csv
"""
from __future__ import annotations

from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
FRACTIONS = np.arange(0.0, 0.42, 0.02)
N_RANDOM = 100
SEED0 = 7000


def build_2024_graph():
    wtw = pd.read_csv(ROOT / "data/processed/wtw_agg_2017_2024.csv", comment="#")
    d = wtw[wtw.year == 2024]
    G = nx.Graph()
    for r in d.itertuples():
        u, v, w = r.exporter_iso3, r.importer_iso3, r.value_kusd * 1e3
        if u == v:
            continue
        if G.has_edge(u, v):
            G[u][v]["weight"] += w
        else:
            G.add_edge(u, v, weight=w)
    return G


def metrics(G, total_w, n0):
    """Three views, which together distinguish fragmentation from amputation:
    - node_share: |LCC| / nodes remaining, the classic percolation question of whether topology holds
    - surv_weight_share: LCC weight / weight remaining, which asks whether surviving trade fragments
    - orig_weight_share: LCC weight / ORIGINAL weight, the value destroyed plus stranded"""
    if G.number_of_edges() == 0 or G.number_of_nodes() == 0:
        return 0.0, 0.0, 0.0
    surv_w = sum(d["weight"] for _, _, d in G.edges(data=True))
    comp = max(nx.connected_components(G), key=lambda c: sum(
        d["weight"] for _, _, d in G.subgraph(c).edges(data=True)))
    w = sum(d["weight"] for _, _, d in G.subgraph(comp).edges(data=True))
    return len(comp) / G.number_of_nodes(), (w / surv_w if surv_w else 0.0), w / total_w


def attack_curve(G, order, total_w):
    H = G.copy()
    n = G.number_of_nodes()
    out = []
    k_removed = 0
    for f in FRACTIONS:
        k_target = int(round(f * n))
        while k_removed < k_target and k_removed < len(order):
            H.remove_node(order[k_removed])
            k_removed += 1
        out.append(metrics(H, total_w, n))
    return out


def main():
    G = build_2024_graph()
    total_w = sum(d["weight"] for _, _, d in G.edges(data=True))
    n = G.number_of_nodes()
    print(f"2024 WTW: {n} nodes, {G.number_of_edges()} edges, total {total_w/1e12:.2f}T USD (pair sums)")

    strength = dict(G.degree(weight="weight"))
    for u, v, d in G.edges(data=True):
        d["dist"] = 1.0 / np.log1p(d["weight"])
    btw = nx.betweenness_centrality(G, weight="dist", normalized=True)

    METRICS = ["lcc_node_share", "lcc_share_of_surviving_weight", "lcc_share_of_original_weight"]
    rows = []
    for name, order in [
        ("targeted_strength", sorted(G, key=lambda x: -strength[x])),
        ("targeted_betweenness", sorted(G, key=lambda x: -btw[x])),
    ]:
        curve = attack_curve(G, order, total_w)
        for f, (m1, m2, m3) in zip(FRACTIONS, curve):
            for mname, val in zip(METRICS, (m1, m2, m3)):
                rows.append((name, mname, f, val, np.nan, np.nan))

    nodes = list(G.nodes)
    rand = np.empty((N_RANDOM, len(FRACTIONS), 3))
    for i in range(N_RANDOM):
        rng = np.random.default_rng(SEED0 + i)
        order = list(rng.permutation(nodes))
        rand[i] = attack_curve(G, order, total_w)
    for k, mname in enumerate(METRICS):
        p50, p5, p95 = (np.percentile(rand[:, :, k], q, axis=0) for q in (50, 5, 95))
        for j, f in enumerate(FRACTIONS):
            rows.append(("random", mname, f, p50[j], p5[j], p95[j]))

    df = pd.DataFrame(rows, columns=["strategy", "metric", "fraction_removed", "value", "p5", "p95"])
    with open(ROOT / "data/processed/attack_curves.csv", "w") as fh:
        fh.write("# source: BACI HS17 V202601 2024 aggregates; analysis/41_attack.py; built 2026-07-30\n"
                 "# metrics: lcc_node_share = |LCC|/remaining nodes (topology holds?);\n"
                 "#   lcc_share_of_surviving_weight = fragmentation of what survives;\n"
                 "#   lcc_share_of_original_weight = value destroyed+stranded (amputation view)\n"
                 "# betweenness distance = 1/ln(1+w); random band = 100 seeds p5-p95\n")
        df.to_csv(fh, index=False)

    def val(strategy, metric, f):
        d = df[(df.strategy == strategy) & (df.metric == metric) & np.isclose(df.fraction_removed, f)]
        return float(d.value.iloc[0])

    print("\nAt 10% node removal (strength-targeted | betweenness | random):")
    for m in METRICS:
        print(f"  {m:<34} {val('targeted_strength', m, 0.10):.3f} | "
              f"{val('targeted_betweenness', m, 0.10):.3f} | {val('random', m, 0.10):.3f}")
    print("At 30% node removal:")
    for m in METRICS:
        print(f"  {m:<34} {val('targeted_strength', m, 0.30):.3f} | "
              f"{val('targeted_betweenness', m, 0.30):.3f} | {val('random', m, 0.30):.3f}")


if __name__ == "__main__":
    main()
