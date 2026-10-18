def is_adjacent(graph, u, v):
    return graph.is_adjacent(u, v)


def build_adjacency_matrix(graph):
    nodes = graph.nodes()
    index = {n: i for i, n in enumerate(nodes)}
    return [[int(graph.is_adjacent(u, v)) for v in nodes] for u in nodes], index
