from ..graph import Graph

def remove_degree_one_vertices(graph):
    """
    Removes all degree-1 vertices iteratively.
    These cannot affect planarity.
    """
    changed = True
    while changed:
        changed = False
        for u in list(graph.nodes()):
            if graph.degree(u) == 1:
                graph.remove_node(u)
                changed = True

def contract_degree_two_vertices(graph):
    """
    For any vertex v with neighbors u and w:
    Replace path u-v-w with a direct edge u-w.
    """
    changed = True
    while changed:
        changed = False
        for v in list(graph.nodes()):
            if graph.degree(v) == 2:
                u, w = list(graph.neighbors(v))
                graph.remove_node(v)
                graph.add_edge(u, w)
                changed = True

def has_parallel_or_self_edges(graph):
    """
    Detect unsupported self-loops. Graph uses sets, so parallel edges cannot
    exist and the two orientations of an undirected edge are not duplicates.
    """
    for u in graph.nodes():
        for v in graph.neighbors(u):
            if u == v:
                return True
    return False

def simplify_graph(graph):
    """
    Applies all simplifications before planarity testing.
    """
    if has_parallel_or_self_edges(graph):
        return False  # unsupported input; not a non-planarity verdict

    remove_degree_one_vertices(graph)
    contract_degree_two_vertices(graph)

    return True
