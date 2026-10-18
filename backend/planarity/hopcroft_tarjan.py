"""Compatibility module: NetworkX's LR test replaces the unfinished HT skeleton."""
import networkx as nx


def is_planar(graph):
    g = nx.Graph()
    g.add_nodes_from(graph.nodes())
    g.add_edges_from(graph.edges())
    return nx.check_planarity(g)[0]
