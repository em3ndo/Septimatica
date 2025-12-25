# backend/layout/force_directed.py
import math
import random

def force_directed_layout(graph, iterations=100, width=500, height=500):
    """
    Simple Fruchterman–Reingold force-directed layout.
    Produces nice-looking graph layouts.
    """
    nodes = graph.nodes()
    pos = {n: (random.random()*width, random.random()*height) for n in nodes}
    k = math.sqrt((width * height) / (len(nodes) + 1))

    def repulsive_force(d):
        return k*k / d if d else k*k

    def attractive_force(d):
        return d*d / k

    for _ in range(iterations):
        disp = {n: [0, 0] for n in nodes}

        # Repulsive forces
        for v in nodes:
            for u in nodes:
                if u == v:
                    continue
                dx = pos[v][0] - pos[u][0]
                dy = pos[v][1] - pos[u][1]
                dist = math.hypot(dx, dy) + 1e-6
                force = repulsive_force(dist)
                disp[v][0] += dx / dist * force
                disp[v][1] += dy / dist * force

        # Attractive forces
        for (u, v) in graph.edges():
            dx = pos[u][0] - pos[v][0]
            dy = pos[u][1] - pos[v][1]
            dist = math.hypot(dx, dy) + 1e-6
            force = attractive_force(dist)
            disp[u][0] -= dx / dist * force
            disp[u][1] -= dy / dist * force
            disp[v][0] += dx / dist * force
            disp[v][1] += dy / dist * force

        # Update positions
        for n in nodes:
            pos[n] = (
                pos[n][0] + disp[n][0],
                pos[n][1] + disp[n][1]
            )

    return pos

