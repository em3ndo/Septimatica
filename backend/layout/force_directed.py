import networkx as nx


def force_directed_layout(graph, iterations=100, width=500, height=500):
    """Stable, cooled force-directed layout including isolated vertices."""
    g = nx.Graph()
    g.add_nodes_from(graph.nodes())
    g.add_edges_from(graph.edges())
    return {n: ((float(p[0]) + 1) * width / 2, (float(p[1]) + 1) * height / 2)
            for n, p in nx.spring_layout(g, seed=42, iterations=iterations).items()}
