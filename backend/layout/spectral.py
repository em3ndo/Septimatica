import numpy as np

def spectral_layout(graph):
    """
    Layout using eigenvectors of graph Laplacian.
    Beautiful and mathematically elegant.

    TODO:
    - Use sparse Laplacian for performance
    """
    n = len(graph.nodes())
    mapping = {node: i for i, node in enumerate(graph.nodes())}

    L = np.zeros((n, n))
    for u in graph.nodes():
        i = mapping[u]
        L[i, i] = graph.degree(u)
        for v in graph.neighbors(u):
            j = mapping[v]
            L[i, j] = -1

    vals, vecs = np.linalg.eigh(L)
    x = vecs[:, 1]
    y = vecs[:, 2] if n > 2 else vecs[:, 1]

    pos = {}
    for node, i in mapping.items():
        pos[node] = (x[i], y[i])
    return pos
