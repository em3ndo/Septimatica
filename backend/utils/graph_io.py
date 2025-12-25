def load_graph_from_edges(edge_list):
    from ..graph import Graph
    g = Graph()
    for u, v in edge_list:
        g.add_edge(u, v)
    return g
