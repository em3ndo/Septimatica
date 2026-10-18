"""Opt in after installing Lean: RUN_LEAN_TESTS=1 python -m pytest -q."""
import os
import networkx as nx
import pytest
from backend.proofs import lean_coloring

pytestmark = pytest.mark.skipif(os.getenv('RUN_LEAN_TESTS') != '1', reason='Local Lean integration is opt-in')


@pytest.mark.parametrize('g', [nx.Graph(), nx.path_graph(2), nx.petersen_graph()])
def test_real_kernel_verification(g):
    colors = nx.coloring.greedy_color(g, strategy='DSATUR')
    assert lean_coloring(g, colors)['status'] == 'verified'


def test_real_kernel_rejects_false_claim():
    # Public API rejects this in Python first. Directly exercise the second checker.
    assert lean_coloring(nx.path_graph(2), {0: 0, 1: 0})['status'] != 'verified'
