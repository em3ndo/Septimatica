# backend/api.py

from .graph import Graph
from .coloring.greedy import greedy_coloring
from .coloring.dsatur import dsatur_coloring
from .planarity.hopcroft_tarjan import is_planar
from .layout.force_directed import force_directed_layout

class SeptimaticaAPI:

    def __init__(self):
        self.graphs = {}  # graph_id -> Graph()

    def create_graph(self, graph_id, edges=None):
        if edges is None:
            edges = []
        g = Graph()
        for u, v in edges:
            g.add_edge(u, v)
        self.graphs[graph_id] = g
        return g

    def add_edge(self, graph_id, u, v):
        if graph_id in self.graphs:
            self.graphs[graph_id].add_edge(u, v)

    def color(self, graph_id, algorithm="dsatur"):
        g = self.graphs[graph_id]
        if algorithm == "greedy":
            return greedy_coloring(g)
        return dsatur_coloring(g)

    def planarity(self, graph_id):
        g = self.graphs[graph_id]
        return is_planar(g)

    def layout(self, graph_id, algorithm="force"):
        g = self.graphs[graph_id]
        if algorithm == "force":
            return force_directed_layout(g)
        raise ValueError("Unknown layout algorithm")

# Global instance
_api = SeptimaticaAPI()

# Exposed functions
create_graph = _api.create_graph
add_edge = _api.add_edge
color_graph = _api.color
test_planarity = _api.planarity
compute_layout = _api.layout