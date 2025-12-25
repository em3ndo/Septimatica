from ..graph import Graph

def test_add_nodes_and_edges():
    g = Graph()
    g.add_edge(1, 2)
    assert 1 in g.adj and 2 in g.adj
    assert 2 in g.neighbors(1)
    assert 1 in g.neighbors(2)

def test_remove_node():
    g = Graph()
    g.add_edge(1, 2)
    g.remove_node(1)
    assert 1 not in g.adj
    assert 1 not in g.neighbors(2)

def test_degree():
    g = Graph()
    g.add_edge(1, 2)
    g.add_edge(1, 3)
    assert g.degree(1) == 2
    assert g.degree(2) == 1
