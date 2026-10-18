import networkx as nx


def spectral_layout(graph):
    """Uses sparse eigensolvers for large inputs; handles zero/one vertex."""
    g = nx.Graph()
    g.add_nodes_from(graph.nodes())
    g.add_edges_from(graph.edges())
    return {n: tuple(map(float, p)) for n, p in nx.spectral_layout(g).items()}
