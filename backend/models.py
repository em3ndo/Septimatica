"""Bounded, shared graph protocol: undirected simple graphs with explicit isolates."""
import hashlib
import json
import networkx as nx
from pydantic import BaseModel, Field, ConfigDict, model_validator


class Node(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    id: int = Field(ge=0, le=1000000, strict=True)
    x: float = Field(default=400, ge=-1e12, le=1e12)
    y: float = Field(default=260, ge=-1e12, le=1e12)


class Edge(BaseModel):
    source: int = Field(ge=0, le=1000000, strict=True)
    target: int = Field(ge=0, le=1000000, strict=True)


class GraphData(BaseModel):
    model_config = ConfigDict(extra='forbid')
    nodes: list[Node] = Field(default_factory=list, max_length=80)
    edges: list[Edge] = Field(default_factory=list, max_length=500)

    @model_validator(mode='after')
    def valid_graph(self):
        ids = {n.id for n in self.nodes}
        if len(ids) != len(self.nodes):
            raise ValueError('Vertex IDs must be unique.')
        seen = set()
        for e in self.edges:
            pair = tuple(sorted((e.source, e.target)))
            if e.source not in ids or e.target not in ids or e.source == e.target or pair in seen:
                raise ValueError('Use distinct existing vertices and no duplicate edges.')
            seen.add(pair)
        return self

    def nx(self):
        g = nx.Graph()
        g.add_nodes_from(n.id for n in self.nodes)
        g.add_edges_from((e.source, e.target) for e in self.edges)
        return g

    def fingerprint(self):
        topology = [sorted(n.id for n in self.nodes), sorted(sorted((e.source, e.target)) for e in self.edges)]
        return hashlib.sha256(json.dumps(topology).encode()).hexdigest()
