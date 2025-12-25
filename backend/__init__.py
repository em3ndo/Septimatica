"""
Septimatica backend package initialization.
Exposes high-level API imports.
"""

from .graph import Graph
from .api import (
    create_graph,
    add_edge,
    color_graph,
    test_planarity,
    compute_layout
)
