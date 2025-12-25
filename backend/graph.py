# backend/graph.py

import numpy as np

class Graph:
    """
    Septimatica Graph
    -----------------
    Dual representation graph supporting:
        - adjacency list (sparse graphs)
        - adjacency matrix (dense graphs)
    Automatically switches representations based on density threshold.
    """

    def __init__(self, density_threshold=0.40):
        # adjacency list representation
        self._adj = {}
        self._nodes = []

        # adjacency matrix representation
        self._adj_matrix = None
        self._use_matrix = False

        # threshold to switch representations
        self._density_threshold = density_threshold

        # cached index mapping for matrix operations
        self._index = {}

    @property
    def adj(self):
        """Expose internal adjacency list for tests and compatibility."""
        return self._adj

    # ----------------------------------------------------------------------
    # Internal utilities and structure synchronization
    # ----------------------------------------------------------------------

    def _num_possible_edges(self):
        n = len(self._nodes)
        return n * (n - 1)

    def density(self):
        """Return the edge density of the graph."""
        m = self.num_edges()
        possible = self._num_possible_edges()
        return 0 if possible == 0 else m / possible

    def _should_use_matrix(self):
        """Check if dense representation should be activated."""
        return self.density() >= self._density_threshold

    def _rebuild_matrix(self):
        """Construct adjacency matrix from adjacency list."""
        n = len(self._nodes)
        mat = np.zeros((n, n), dtype=np.uint8)

        index = {node: i for i, node in enumerate(self._nodes)}
        self._index = index

        for u in self._nodes:
            i = index[u]
            for v in self._adj[u]:
                j = index[v]
                mat[i, j] = 1
                mat[j, i] = 1

        self._adj_matrix = mat

    def _ensure_representation(self):
        """Ensure the correct representation is active."""
        use_matrix = self._should_use_matrix()

        if use_matrix and not self._use_matrix:
            self._use_matrix = True
            self._rebuild_matrix()

        elif not use_matrix and self._use_matrix:
            # tear down matrix → revert to adjacency list only
            self._use_matrix = False
            self._adj_matrix = None
            self._index = {}

    # ----------------------------------------------------------------------
    # Core graph manipulation
    # ----------------------------------------------------------------------

    def add_node(self, node):
        if node in self._adj:
            return

        self._adj[node] = set()
        self._nodes.append(node)

        # representation may need refreshing
        if self._use_matrix:
            self._rebuild_matrix()
        else:
            self._ensure_representation()

    def add_edge(self, u, v):
        if u == v:
            raise ValueError("Self-loops are not supported.")

        if u not in self._adj:
            self.add_node(u)
        if v not in self._adj:
            self.add_node(v)

        if v not in self._adj[u]:
            self._adj[u].add(v)
            self._adj[v].add(u)

            # update matrix if needed
            if self._use_matrix:
                i = self._index[u]
                j = self._index[v]
                self._adj_matrix[i, j] = 1
                self._adj_matrix[j, i] = 1

        self._ensure_representation()

    def remove_edge(self, u, v):
        if u in self._adj and v in self._adj[u]:
            self._adj[u].remove(v)
            self._adj[v].remove(u)

            if self._use_matrix:
                i = self._index[u]
                j = self._index[v]
                self._adj_matrix[i, j] = 0
                self._adj_matrix[j, i] = 0

        self._ensure_representation()

    def remove_node(self, node):
        if node not in self._adj:
            return

        # remove edges
        for v in list(self._adj[node]):
            self._adj[v].remove(node)

        del self._adj[node]
        self._nodes.remove(node)

        self._ensure_representation()

    # ----------------------------------------------------------------------
    # Queries
    # ----------------------------------------------------------------------

    def nodes(self):
        return list(self._nodes)

    def edges(self):
        seen = set()
        result = []
        for u in self._nodes:
            for v in self._adj[u]:
                if (v, u) not in seen:
                    seen.add((u, v))
                    result.append((u, v))
        return result

    def num_nodes(self):
        return len(self._nodes)

    def num_edges(self):
        return sum(len(neigh) for neigh in self._adj.values()) // 2

    # ----------------------------------------------------------------------
    # Degree + neighbor APIs (matrix-optimized when dense)
    # ----------------------------------------------------------------------

    def neighbors(self, node):
        """Return neighbors of a node, optimized for matrix mode."""
        if not self._use_matrix:
            return list(self._adj[node])

        idx = self._index[node]
        row = self._adj_matrix[idx]
        return [self._nodes[i] for i in np.where(row == 1)[0]]

    def degree(self, node):
        if not self._use_matrix:
            return len(self._adj[node])
        idx = self._index[node]
        return int(self._adj_matrix[idx].sum())

    # ----------------------------------------------------------------------
    # Utility for BFS, DFS, coloring, planarity modules
    # ----------------------------------------------------------------------

    def is_adjacent(self, u, v):
        if not self._use_matrix:
            return v in self._adj[u]
        return bool(self._adj_matrix[self._index[u], self._index[v]])

    def to_adjacency_matrix(self):
        """Return adjacency matrix view regardless of internal mode."""
        if not self._use_matrix:
            self._rebuild_matrix()
        return np.copy(self._adj_matrix)
