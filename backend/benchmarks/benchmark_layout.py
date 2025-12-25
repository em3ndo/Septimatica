import time
import random
import networkx as nx
from ..graph import Graph
from ..layout.force_directed import fruchterman_reingold

def generate_graph(n, p=0.1):
    G = Graph()
    for i in range(n):
        for j in range(i+1, n):
            if random.random() < p:
                G.add_edge(i, j)
    return G

def benchmark_layout():
    G = generate_graph(100)

    start = time.time()
    fruchterman_reingold(G)
    print("Septimatica FR:", time.time() - start)

    NX = nx.Graph(G.edges())
    start = time.time()
    nx.spring_layout(NX)
    print("NetworkX FR:", time.time() - start)

if __name__ == "__main__":
    benchmark_layout()
