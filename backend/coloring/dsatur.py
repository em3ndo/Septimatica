# backend/coloring/dsatur.py

def dsatur_coloring(graph):
    """
    DSATUR algorithm.
    Dominating heuristic for coloring.
    """
    colors = {}
    sat = {u: 0 for u in graph.nodes()}  # saturation degrees
    degrees = {u: graph.degree(u) for u in graph.nodes()}

    while len(colors) < len(graph.nodes()):
        # Pick uncolored node with max saturation (break ties with degree)
        u = max(
            (n for n in graph.nodes() if n not in colors),
            key=lambda x: (sat[x], degrees[x])
        )

        # Assign smallest available color
        neighbor_colors = {colors[n] for n in graph.neighbors(u) if n in colors}
        c = 0
        while c in neighbor_colors:
            c += 1
        colors[u] = c

        # Update saturation for neighbors
        for v in graph.neighbors(u):
            if v not in colors:
                sat[v] = len({colors[n] for n in graph.neighbors(v) if n in colors})

    return colors
