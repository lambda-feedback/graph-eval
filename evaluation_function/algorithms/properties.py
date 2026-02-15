"""Simple graph property checks."""

from __future__ import annotations

from evaluation_function.schemas import Graph

from .connectivity import connectivity_info
from .cycles import cycle_info
from .utils import node_ids


def _simple_adj(graph: Graph) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = {n.id: set() for n in graph.nodes}
    for e in graph.edges:
        adj[e.source].add(e.target)
        if not graph.directed:
            adj[e.target].add(e.source)
    return adj


def is_tree(graph: Graph) -> bool:
    return connectivity_info(graph).is_connected and not cycle_info(graph).has_cycle


def is_forest(graph: Graph) -> bool:
    return not cycle_info(graph).has_cycle


def is_dag(graph: Graph) -> bool:
    return bool(graph.directed) and not cycle_info(graph).has_cycle


def degree_sequence(graph: Graph) -> list[int]:
    adj = _simple_adj(graph)
    return sorted((len(adj[n]) for n in node_ids(graph)), reverse=True)


def is_regular(graph: Graph) -> bool:
    seq = degree_sequence(graph)
    return len(set(seq)) <= 1


def is_complete(graph: Graph) -> bool:
    n = len(graph.nodes)
    if n <= 1:
        return True
    adj = _simple_adj(graph)
    return all(len(adj[nid]) == n - 1 for nid in adj)


def is_eulerian(graph: Graph) -> bool:
    """Has an Euler circuit (closed walk visiting every edge exactly once)."""
    ids = node_ids(graph)
    if not ids:
        return True

    if graph.directed:
        if not connectivity_info(graph, connectivity_type="weakly_connected").is_connected:
            return False
        in_deg: dict[str, int] = {n: 0 for n in ids}
        out_deg: dict[str, int] = {n: 0 for n in ids}
        for e in graph.edges:
            out_deg[e.source] += 1
            in_deg[e.target] += 1
        return all(in_deg[n] == out_deg[n] for n in ids)

    if not connectivity_info(graph).is_connected:
        return False
    adj = _simple_adj(graph)
    return all(len(adj[n]) % 2 == 0 for n in ids)


def is_semi_eulerian(graph: Graph) -> bool:
    """Has an Euler path (walk visiting every edge exactly once, possibly open)."""
    ids = node_ids(graph)
    if not ids:
        return True

    if graph.directed:
        if not connectivity_info(graph, connectivity_type="weakly_connected").is_connected:
            return False
        in_deg: dict[str, int] = {n: 0 for n in ids}
        out_deg: dict[str, int] = {n: 0 for n in ids}
        for e in graph.edges:
            out_deg[e.source] += 1
            in_deg[e.target] += 1
        diffs = [out_deg[n] - in_deg[n] for n in ids]
        # Eulerian circuit (all zero) or Euler path (one +1, one -1, rest 0)
        return sorted(diffs) in [
            [0] * len(ids),
            [-1] + [0] * (len(ids) - 2) + [1],
        ]

    if not connectivity_info(graph).is_connected:
        return False
    adj = _simple_adj(graph)
    odd = sum(1 for n in ids if len(adj[n]) % 2 != 0)
    return odd == 0 or odd == 2


def is_subgraph(sub: Graph, parent: Graph) -> bool:
    """Check if sub is a subgraph of parent."""
    parent_nodes = {n.id for n in parent.nodes}
    if not {n.id for n in sub.nodes} <= parent_nodes:
        return False
    parent_edges: set[tuple[str, str]] = set()
    for e in parent.edges:
        parent_edges.add((e.source, e.target))
        if not parent.directed:
            parent_edges.add((e.target, e.source))
    for e in sub.edges:
        key = (e.source, e.target)
        if key not in parent_edges:
            if sub.directed or (e.target, e.source) not in parent_edges:
                return False
    return True
