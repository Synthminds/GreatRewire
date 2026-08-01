#!/usr/bin/env python3
"""This script holds fixed the machine that explained the last
twenty-five years of the world trade web and run it forward as a null for a world that never
rewired. To achieve this objective we port that machine to Python here, reproducing Equations
2-8 exactly as published so the null carries no discretion of ours.

Kennedy, Wish, Smith, Sherrell, Shields & Gera, "Building a Reliable,
Dynamic and Temporal Synthetic Model of the World Trade Web" (CompleNet 2022).
We document parameter provenance and the two typo resolutions in
notes/completnet-spec.md.

Conventions:
- We represent the undirected weighted network as a symmetric N x N numpy array (0 = no edge).
- w = GDP vector in any consistent unit, since fitness normalizes by the mean.
- Weights live in "model units" (Eq. 4 scale). Consult spec caveat 2 before
  mixing them with real trade values.
- We route all randomness through a single numpy Generator for reproducibility.

Self-test: python3 wtw_model.py  (unit checks on Eq. 7 continuity, clamps, Eq. 8 bounds)
"""
from __future__ import annotations

import numpy as np

PARAMS = dict(
    alpha0=220.0, beta0=80.0,      # Eq. 3 initialization (Nelder-Mead fit, paper 4.1)
    alpha=200.0, beta=80.0,        # Eq. 5 growth-year creation (paper 3.4)
    gamma_shape=6.5571,            # Eq. 4  F ~ Gamma(shape, scale)  (paper Fig. 1)
    gamma_scale=0.57943,
    del_a=-0.048303, del_b=-0.96089, del_c=-5.2225,   # Eq. 7 quadratic (paper Fig. 2)
    del_floor_y=-10.0, del_floor_p=0.36,              # a ratio below 1e-10 yields P_D = curve max
    eq8_band=0.05, eq8_jitter=(0.95, 1.05),           # Eq. 8 thresholds
    eq8_factor_floor=0.05,         # our guard for r <= -50%, which the paper leaves undefined
)


class WTWModel:
    def __init__(self, seed=None, **overrides):
        self.p = {**PARAMS, **overrides}
        self.rng = np.random.default_rng(seed)

    # ---- pieces -----------------------------------------------------------
    @staticmethod
    def fitness(w):
        """Eq. 2: x_i = w_i / mean(w)."""
        w = np.asarray(w, dtype=float)
        return w / w.mean()

    def link_prob(self, x, alpha, beta):
        """Eq. 3/5: P_L = a x_i x_j / (1 + b x_i x_j), clamped to [0, 1]."""
        xx = np.outer(x, x)
        return np.clip(alpha * xx / (1.0 + beta * xx), 0.0, 1.0)

    def draw_weights(self, wmin_flat):
        """Eq. 4: e = 10^-F * min(w_i, w_j), F ~ Gamma(shape, scale)."""
        F = self.rng.gamma(self.p["gamma_shape"], self.p["gamma_scale"], size=wmin_flat.size)
        return 10.0 ** (-F) * wmin_flat

    def deletion_prob(self, e_flat, wsum_flat):
        """Eq. 6-7. y = log10(e / (w_i + w_j)), a quadratic law with a 0.36 floor below y=-10."""
        y = np.log10(e_flat / wsum_flat)
        p = self.p
        quad = 10.0 ** (p["del_a"] * y**2 + p["del_b"] * y + p["del_c"])
        return np.where(y >= p["del_floor_y"], quad, p["del_floor_p"])

    def adjust_factor(self, r_flat):
        """Eq. 8 multiplicative factor. We draw it per edge from the r-dependent uniform range."""
        p = self.p
        lo = np.where(r_flat > p["eq8_band"], 1.0,
             np.where(r_flat < -p["eq8_band"],
                      np.maximum(1.0 + 2.0 * r_flat, p["eq8_factor_floor"]),
                      p["eq8_jitter"][0]))
        hi = np.where(r_flat > p["eq8_band"], 1.0 + 2.0 * r_flat,
             np.where(r_flat < -p["eq8_band"], 1.0, p["eq8_jitter"][1]))
        u = self.rng.random(r_flat.size)
        return lo + u * (hi - lo)

    # ---- lifecycle --------------------------------------------------------
    def init_year(self, w):
        """Initialize the base-year network (Eq. 2-4 with alpha0/beta0)."""
        w = np.asarray(w, dtype=float)
        n = w.size
        x = self.fitness(w)
        P = self.link_prob(x, self.p["alpha0"], self.p["beta0"])
        iu = np.triu_indices(n, 1)
        made = self.rng.random(iu[0].size) < P[iu]
        wmin = np.minimum(w[iu[0]], w[iu[1]])
        e = np.zeros(iu[0].size)
        e[made] = self.draw_weights(wmin[made])
        A = np.zeros((n, n))
        A[iu] = e
        return A + A.T

    def step(self, A, w_now, w_prev):
        """Step one year forward: we create (Eq. 5+4), delete (Eq. 6-7), then adjust (Eq. 8)."""
        w_now = np.asarray(w_now, dtype=float)
        w_prev = np.asarray(w_prev, dtype=float)
        n = w_now.size
        x = self.fitness(w_now)
        iu = np.triu_indices(n, 1)
        e = A[iu].copy()
        exists = e > 0

        # we delete and adjust existing edges against current-year GDPs
        if exists.any():
            wsum = (w_now[iu[0]] + w_now[iu[1]])[exists]
            pd = self.deletion_prob(e[exists], wsum)
            kill = self.rng.random(pd.size) < pd
            wmin_now = np.minimum(w_now[iu[0]], w_now[iu[1]])[exists]
            wmin_prev = np.minimum(w_prev[iu[0]], w_prev[iu[1]])[exists]
            r = (wmin_now - wmin_prev) / wmin_prev
            factor = self.adjust_factor(r)
            new_vals = np.where(kill, 0.0, e[exists] * factor)
            e[exists] = new_vals

        # we create edges across currently-unconnected pairs (alpha/beta), weighting via Eq. 4
        P = self.link_prob(x, self.p["alpha"], self.p["beta"])
        vacant = ~exists
        made = vacant & (self.rng.random(iu[0].size) < P[iu])
        if made.any():
            wmin = np.minimum(w_now[iu[0]], w_now[iu[1]])[made]
            e[made] = self.draw_weights(wmin)

        A2 = np.zeros_like(A)
        A2[iu] = e
        return A2 + A2.T

    def run(self, W, connectivity=False):
        """W: (n_countries, n_years) GDP matrix. We return the list of yearly adjacency matrices."""
        out = [self.init_year(W[:, 0])]
        for t in range(1, W.shape[1]):
            A = self.step(out[-1], W[:, t], W[:, t - 1])
            if connectivity:
                A = self.enforce_connectivity(A, W[:, t])
            out.append(A)
        return out

    def enforce_connectivity(self, A, w):
        """Paper 3.5: we bridge components with random pairs carrying Eq. 4 weights."""
        import networkx as nx
        G = nx.from_numpy_array((A > 0).astype(int))
        comps = list(nx.connected_components(G))
        while len(comps) > 1:
            c1 = list(comps[0]); c2 = list(comps[1])
            i = int(self.rng.choice(c1)); j = int(self.rng.choice(c2))
            A[i, j] = A[j, i] = self.draw_weights(np.array([min(w[i], w[j])]))[0]
            G.add_edge(i, j)
            comps = list(nx.connected_components(G))
        return A


def unweighted_stats(A):
    """Yield the paper 4.4 statistics on the unweighted undirected graph."""
    import networkx as nx
    G = nx.from_numpy_array((A > 0).astype(np.int8))
    n = G.number_of_nodes()
    E = G.number_of_edges()
    deg = np.fromiter((d for _, d in G.degree()), dtype=float, count=n)
    comp = max(nx.connected_components(G), key=len)
    H = G.subgraph(comp)
    sp = []
    for _, dd in nx.all_pairs_shortest_path_length(H):
        sp.extend(v for v in dd.values() if v > 0)
    sp = np.asarray(sp, dtype=float)
    cc = np.fromiter(nx.clustering(G).values(), dtype=float, count=n)
    return dict(
        E=E, density=2.0 * E / (n * (n - 1)),
        mu_deg=deg.mean(), sd_deg=deg.std(),
        mu_sp=sp.mean() if sp.size else np.nan, sd_sp=sp.std() if sp.size else np.nan,
        mu_cc=cc.mean(), sd_cc=cc.std(),
        kcore=max(nx.core_number(G).values()),
        lcc_share=len(comp) / n,
    )


def _selftest():
    m = WTWModel(seed=1)
    # Eq. 7 continuity at the floor: we verify the quadratic at y = -10 equals 0.36 to 3 dp
    p = PARAMS
    q_at_floor = 10.0 ** (p["del_a"] * 100 - p["del_b"] * 10 + p["del_c"])
    assert abs(q_at_floor - 0.361) < 0.002, q_at_floor
    # the parabola's vertex sits at the floor: y* = -b/2a, approximately -9.95
    assert abs(-p["del_b"] / (2 * p["del_a"]) + 9.95) < 0.06
    # P_L must clamp at 1 for giant economies
    x = np.array([50.0, 40.0, 0.1])
    assert m.link_prob(x, 220, 80).max() == 1.0
    # Eq. 8 factor bounds
    r = np.array([0.10, -0.10, 0.0, -0.60])
    f = m.adjust_factor(r)
    assert 1.0 <= f[0] <= 1.2 and 0.8 <= f[1] <= 1.0 and 0.95 <= f[2] <= 1.05 and f[3] >= p["eq8_factor_floor"]
    # smoke test: a 50-country, 3-year run, enough to catch a shape error
    W = np.abs(np.random.default_rng(0).lognormal(23.2, 2.46, size=(50, 3)))
    nets = m.run(W)
    assert len(nets) == 3 and (nets[-1] >= 0).all()
    print("wtw_model selftest: ALL PASS")


if __name__ == "__main__":
    _selftest()
