# backend/coloring/greedy.py

def greedy_coloring(graph):
    """
    Greedy coloring: simple but surprisingly effective on many graphs.
    """
    colors = {}
    for node in sorted(graph.nodes(), key=lambda x: graph.degree(x), reverse=True):
        neighbor_colors = {colors[n] for n in graph.neighbors(node) if n in colors}
        color = 0
        while color in neighbor_colors:
            color += 1
        colors[node] = color
    return colors
