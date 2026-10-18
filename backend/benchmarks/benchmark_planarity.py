import time
import networkx as nx
from ..graph import Graph
from ..planarity import is_planar

def benchmark_planarity():
    # classic planar graph
    edges = [(0,1),(1,2),(2,3),(3,0),(0,2)]
    G = Graph()
    for e in edges:
        G.add_edge(*e)

    try:
        start = time.time()
        is_planar(G)
        print("Septimatica planarity:", time.time() - start)
    except NotImplementedError:
        print("Septimatica planarity not implemented yet")

    NX = nx.Graph(edges)
    start = time.time()
    nx.check_planarity(NX)
    print("NetworkX planarity:", time.time() - start)

if __name__ == "__main__":
    benchmark_planarity()
