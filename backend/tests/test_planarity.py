from ..graph import Graph
from ..planarity import is_planar

def test_planarity_k5():
    g = Graph()
    for i in range(5):
        for j in range(i+1, 5):
            g.add_edge(i, j)

    assert is_planar(g) is False
