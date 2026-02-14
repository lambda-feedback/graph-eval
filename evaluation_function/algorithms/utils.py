from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from evaluation_function.schemas import Edge, Graph


@dataclass(frozen=True)
class AdjEdge:
    to: str
    weight: float
    edge: Edge


def node_ids(graph: Graph) -> list[str]:
    return [n.id for n in graph.nodes]


def build_adjacency(graph: Graph, *, undirected: bool) -> dict[str, list[AdjEdge]]:
    adj: dict[str, list[AdjEdge]] = {n.id: [] for n in graph.nodes}
    for e in graph.edges:
        w = float(e.weight if e.weight is not None else 1.0)
        adj.setdefault(e.source, []).append(AdjEdge(to=e.target, weight=w, edge=e))
        if undirected:
            adj.setdefault(e.target, []).append(AdjEdge(to=e.source, weight=w, edge=e))
    return adj


def build_reverse_adjacency(graph: Graph) -> dict[str, list[AdjEdge]]:
    """Directed reverse adjacency (for strongly connected checks)."""
    adj: dict[str, list[AdjEdge]] = {n.id: [] for n in graph.nodes}
    for e in graph.edges:
        w = float(e.weight if e.weight is not None else 1.0)
        adj.setdefault(e.target, []).append(AdjEdge(to=e.source, weight=w, edge=e))
    return adj


def edge_weight_lookup(graph: Graph, *, undirected: bool) -> dict[tuple[str, str], float]:
    """Lookup of min weight for (u,v). Useful for validating user-provided paths."""
    lookup: dict[tuple[str, str], float] = {}
    for e in graph.edges:
        w = float(e.weight if e.weight is not None else 1.0)
        key = (e.source, e.target)
        lookup[key] = min(lookup.get(key, w), w)
        if undirected:
            key2 = (e.target, e.source)
            lookup[key2] = min(lookup.get(key2, w), w)
    return lookup


def path_weight(path: Iterable[str], w_lookup: dict[tuple[str, str], float]) -> Optional[float]:
    path_list = list(path)
    if len(path_list) <= 1:
        return 0.0
    total = 0.0
    for u, v in zip(path_list, path_list[1:]):
        w = w_lookup.get((u, v))
        if w is None:
            return None
        total += w
    return total

