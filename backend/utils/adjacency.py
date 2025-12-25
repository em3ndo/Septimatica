# backend/utils/adjacency.py

def build_adjacency_matrix(graph):
    nodes = graph.nodes()
    index = {n: i for i, n in enumerate(nodes)}
    n = len(nodes)
    mat = [[0] * n for _ in range(n)]

    for u in nodes:
        for v in graph.neighbors(u):
            mat[index[u]][index[v]] = 1

    return mat, index
