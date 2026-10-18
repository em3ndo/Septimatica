"""Deterministic graph analysis; exact coloring is bounded, never mislabeled."""
import time
import networkx as nx

TOPICS = ('coloring', 'planarity', 'bipartite', 'connectivity', 'eulerian')


def coloring(g, seconds=0.4):
    if not g:
        return {'colors': {}, 'lower_bound': 0, 'upper_bound': 0, 'exact': True}
    best = nx.coloring.greedy_color(g, strategy='DSATUR')
    upper = max(best.values()) + 1
    # A greedy clique gives a certified lower bound without exponential enumeration.
    clique = []
    for v in sorted(g, key=g.degree, reverse=True):
        if all(g.has_edge(v, u) for u in clique):
            clique.append(v)
    lower = len(clique)
    if nx.is_bipartite(g):
        best = nx.bipartite.color(g)
        if not g.number_of_edges():
            best = {v: 0 for v in g}
        upper = 2 if g.number_of_edges() else 1
        lower = upper
    deadline = time.monotonic() + seconds
    if len(g) <= 24:
        for k in range(lower, upper):
            assigned = {}

            def search():
                if time.monotonic() > deadline:
                    raise TimeoutError
                if len(assigned) == len(g):
                    return True
                v = max((v for v in g if v not in assigned),
                        key=lambda v: (len({assigned[u] for u in g[v] if u in assigned}), g.degree(v)))
                forbidden = {assigned[u] for u in g[v] if u in assigned}
                for c in range(min(k, max(assigned.values(), default=-1) + 2)):
                    if c not in forbidden:
                        assigned[v] = c
                        if search():
                            return True
                        del assigned[v]
                return False

            try:
                if search():
                    best, upper = dict(assigned), k
                    break
                lower = k + 1
            except TimeoutError:
                break
    return {'colors': best, 'lower_bound': lower, 'upper_bound': upper, 'exact': lower == upper}


def analyze(g, topic):
    if topic == 'coloring':
        return coloring(g)
    if topic == 'planarity':
        planar, embedding = nx.check_planarity(g)
        return {'planar': planar, 'embedding': embedding.get_data() if planar else None,
                'method': 'NetworkX Left-Right planarity test'}
    if topic == 'bipartite':
        yes = nx.is_bipartite(g)
        return {'bipartite': yes, 'colors': nx.bipartite.color(g) if yes else None}
    if topic == 'connectivity':
        return {'components': [sorted(c) for c in nx.connected_components(g)],
                'tree': bool(g) and nx.is_tree(g), 'degrees': dict(g.degree())}
    if topic == 'eulerian':
        # Ignore isolates for edge-covering walks; document this convention in the UI.
        active = g.subgraph([n for n in g if g.degree(n)])
        circuit = bool(active) and nx.is_eulerian(active)
        trail = bool(active) and nx.has_eulerian_path(active)
        return {'circuit': circuit, 'trail': trail,
                'walk': list(nx.eulerian_path(active)) if trail else [],
                'convention': 'Isolated vertices are ignored; an edgeless graph has no nonempty walk.'}
    raise ValueError('Unknown topic')
