from fastapi import FastAPI
from pydantic import BaseModel
from .api import (
    create_graph, add_edge, color_graph,
    test_planarity, compute_layout
)

app = FastAPI()

class Edge(BaseModel):
    u: int
    v: int

class GraphRequest(BaseModel):
    graph_id: str
    edges: list[Edge]

@app.post("/create_graph")
def create_graph_endpoint(req: GraphRequest):
    g = create_graph(req.graph_id)
    for e in req.edges:
        add_edge(req.graph_id, e.u, e.v)
    return {"status": "success"}

@app.get("/color/{graph_id}")
def color_endpoint(graph_id: str):
    return color_graph(graph_id)

@app.get("/planarity/{graph_id}")
def planarity_endpoint(graph_id: str):
    return {"planar": test_planarity(graph_id)}

@app.get("/layout/{graph_id}")
def layout_endpoint(graph_id: str, method="force"):
    return compute_layout(graph_id, layout=method)
