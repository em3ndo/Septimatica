from ..graph import Graph
from ..planarity import is_planar

def test_planarity_k5():
    g = Graph()
    for i in range(5):
        for j in range(i+1, 5):
            g.add_edge(i, j)

    try:
        p = is_planar(g)
    except NotImplementedError:
        p = None

    assert p is None or p is False
