import time
import random
import networkx as nx
from ..graph import Graph
from ..coloring.dsatur import dsatur_coloring
from ..coloring.greedy import greedy_coloring

def generate_random_graph(n, p):
    G = Graph()
    for i in range(n):
        for j in range(i+1, n):
            if random.random() < p:
                G.add_edge(i, j)
    return G

def benchmark_dsatur_vs_networkx():
    sizes = [50, 100, 200]
    densities = [0.1, 0.2, 0.5]
    for n in sizes: # Iterate over graph sizes
        for p in densities: # Iterate over graph densities
            print(f"\n=== Graph size: {n}, Density: {p} ===")

            G = generate_random_graph(n, p)

            # Septimatica DSATUR
            start = time.time()
            dsatur_coloring(G)
            print("Septimatica DSATUR:", round(time.time() - start, 4), "seconds")

            # NetworkX DSATUR
            NX = nx.Graph(G.edges())
            start = time.time()
            nx.coloring.greedy_color(NX, strategy="saturation_largest_first")
            print("NetworkX DSATUR:", round(time.time() - start, 4), "seconds")

            # Septimatica Greedy
            start = time.time()
            greedy_coloring(G)
            print("Septimatica Greedy:", round(time.time() - start, 4), "seconds")

            # NetworkX Greedy
            start = time.time()
            nx.coloring.greedy_color(NX, strategy="largest_first")
            print("NetworkX Greedy:", round(time.time() - start, 4), "seconds")

if __name__ == "__main__":
    benchmark_dsatur_vs_networkx()
