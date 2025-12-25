from ..graph import Graph
from ..layout.force_directed import force_directed_layout
from ..layout.spectral import spectral_layout

def test_force_directed_layout():
    g = Graph()
    g.add_edge(1, 2)
    pos = force_directed_layout(g)
    assert len(pos) == 2

def test_spectral_layout():
    g = Graph()
    g.add_edge(1, 2)
    pos = spectral_layout(g)
    assert len(pos) == 2
