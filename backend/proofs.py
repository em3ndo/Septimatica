"""Check student witnesses, then optionally kernel-check concrete coloring facts.

Never execute student or LLM-generated Lean. Only integers enter fixed templates.
Lean validates the coloring witness, not the student's prose or minimality.
"""
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from threading import BoundedSemaphore
import networkx as nx

_LEAN_SLOTS = BoundedSemaphore(2)


def lean_coloring(g, colors):
    executable = os.getenv('LEAN_BIN', 'lean')
    if not shutil.which(executable):
        return {'status': 'unavailable', 'scope': 'proper coloring only'}
    vertices = ', '.join(str(v) for v in sorted(g))
    edges = ', '.join(f'({u}, {v})' for u, v in g.edges())
    branches = '\n'.join(f'  | {v} => {colors[v]}' for v in sorted(g))
    bound = max(colors.values(), default=-1) + 1
    source = f'''import Std
set_option maxHeartbeats 400000
def vertices : List Nat := [{vertices}]
def edges : List (Nat × Nat) := [{edges}]
def color : Nat → Nat
{branches}
  | _ => 0
theorem proper : ∀ e ∈ edges, color e.1 ≠ color e.2 := by decide
theorem bounded : ∀ v ∈ vertices, color v < {bound} := by decide
'''
    if not _LEAN_SLOTS.acquire(blocking=False):
        return {'status': 'unavailable', 'scope': 'Compiler busy; Python certificate check still applies.'}
    try:
        with tempfile.TemporaryDirectory(prefix='septimatica-lean-') as folder:
            path = Path(folder) / 'Certificate.lean'
            path.write_text(source)
            result = subprocess.run([executable, '-M', '1024', str(path)],
                                    capture_output=True, text=True, timeout=12, cwd=folder)
        status = 'verified' if result.returncode == 0 else 'unavailable'
    except (OSError, subprocess.TimeoutExpired):
        status = 'unavailable'
    finally:
        _LEAN_SLOTS.release()
    return {'status': status, 'scope': 'proper coloring and stated color upper bound; not minimality or prose',
            'source': source}


def certificate(g, topic, witness):
    """Return evidence for a claim; reject malformed witnesses without guessing."""
    def require(condition):
        if not condition:
            raise ValueError('Invalid certificate')

    try:
        if topic in ('coloring', 'bipartite') and 'colors' in witness:
            colors = {int(v): c for v, c in witness['colors'].items()}
            require(set(colors) == set(g))
            require(all(type(c) is int and 0 <= c < 80 for c in colors.values()))
            require(all(colors[u] != colors[v] for u, v in g.edges()))
            if topic == 'bipartite':
                require(len(set(colors.values())) <= 2)
            return {'valid': True, 'claim': 'Proper coloring witness (upper bound only).',
                    'lean': lean_coloring(g, colors)}
        if topic == 'bipartite' and 'odd_cycle' in witness:
            cycle = witness['odd_cycle']
            require(len(cycle) >= 3 and len(cycle) % 2 == 1 and len(set(cycle)) == len(cycle))
            require(all(g.has_edge(cycle[i], cycle[(i+1) % len(cycle)]) for i in range(len(cycle))))
            return {'valid': True, 'claim': 'Odd cycle certifies non-bipartiteness.'}
        if topic == 'planarity' and 'rotation' in witness:
            rotation = {int(v): ns for v, ns in witness['rotation'].items()}
            require(set(rotation) == set(g))
            require(all(len(ns) == len(set(ns)) and set(ns) == set(g[v]) for v, ns in rotation.items()))
            embedding = nx.PlanarEmbedding()
            embedding.set_data(rotation)
            embedding.add_nodes_from(g)
            embedding.check_structure()
            return {'valid': True, 'claim': 'Valid planar rotation system (algorithmically checked).'}
        if topic == 'planarity' and 'branch_sets' in witness:
            # Disjoint connected branch sets certify a K5 or K3,3 minor.
            parts = [set(p) for p in witness['branch_sets']]
            require(len(parts) in (5, 6) and all(parts))
            require(sum(map(len, parts)) == len(set.union(*parts)))
            require(set.union(*parts) <= set(g))
            require(all(nx.is_connected(g.subgraph(p)) for p in parts))
            pairs = [(i, j) for i in range(5) for j in range(i+1, 5)] if len(parts) == 5 else [(i, j) for i in range(3) for j in range(3, 6)]
            require(all(any(g.has_edge(u, v) for u in parts[i] for v in parts[j]) for i, j in pairs))
            return {'valid': True, 'claim': 'K5 or K3,3 minor certifies non-planarity (algorithmically checked).'}
    except (AssertionError, ValueError, TypeError, KeyError, AttributeError, nx.NetworkXException):
        return {'valid': False, 'claim': 'The witness does not establish this claim. Recheck its vertices and edges.'}
    return {'valid': False, 'claim': 'Use a supported certificate or request instructor review of your written proof.'}
