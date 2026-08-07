from ..graph import Graph
from ..coloring.greedy import greedy_coloring
from ..coloring.dsatur import dsatur_coloring
import unittest

class TestColoring(unittest.TestCase):
    def test_greedy_coloring_simple(self):
        g = Graph()
        g.add_edge(1, 2)
        col = greedy_coloring(g)
        assert col[1] != col[2]

    def test_dsatur_coloring_complete_graph(self):
        g = Graph()
        nodes = [1, 2, 3, 4]
        for i in nodes:
            for j in nodes:
                if i < j:
                    g.add_edge(i, j)
        col = dsatur_coloring(g)
        assert len(set(col.values())) == len(nodes)
