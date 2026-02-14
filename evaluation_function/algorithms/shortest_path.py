from __future__ import annotations

import heapq
from typing import Literal, Optional

from evaluation_function.schemas import Graph, PathResult

from .utils import build_adjacency, edge_weight_lookup, node_ids, path_weight


ShortestPathAlgorithm = Literal["bfs", "dijkstra", "bellman_ford", "auto"]


class NegativeCycleError(Exception):
    pass


def _reconstruct_path(parent: dict[str, str], source: str, target: str) -> Optional[list[str]]:
    if source == target:
        return [source]
    if target not in parent:
        return None
    cur = target
    out: list[str] = [cur]
    while cur != source:
        cur = parent[cur]
        out.append(cur)
    out.reverse()
    return out


def _bfs_shortest_path(graph: Graph, source: str, target: str, *, undirected: bool) -> PathResult:
    from collections import deque

    adj = build_adjacency(graph, undirected=undirected)
    if source not in adj or target not in adj:
        return PathResult(algorithm_used="bfs", path_exists=False)
    q = deque([source])
    parent: dict[str, str] = {}
    dist: dict[str, int] = {source: 0}
    while q:
        u = q.popleft()
        if u == target:
            break
        for ae in adj.get(u, []):
            v = ae.to
            if v not in dist:
                dist[v] = dist[u] + 1
                parent[v] = u
                q.append(v)
    if target not in dist:
        return PathResult(algorithm_used="bfs", path_exists=False)
    path = _reconstruct_path(parent, source, target)
    return PathResult(algorithm_used="bfs", path_exists=True, distance=float(dist[target]), path=path)


def _dijkstra_shortest_path(graph: Graph, source: str, target: str, *, undirected: bool) -> PathResult:
    adj = build_adjacency(graph, undirected=undirected)
    if source not in adj or target not in adj:
        return PathResult(algorithm_used="dijkstra", path_exists=False)

    dist: dict[str, float] = {source: 0.0}
    parent: dict[str, str] = {}
    pq: list[tuple[float, str]] = [(0.0, source)]
    seen: set[str] = set()

    while pq:
        d, u = heapq.heappop(pq)
        if u in seen:
            continue
        seen.add(u)
        if u == target:
            break
        for ae in adj.get(u, []):
            if ae.weight < 0:
                raise ValueError("Dijkstra cannot be used with negative edge weights.")
            nd = d + ae.weight
            if nd < dist.get(ae.to, float("inf")):
                dist[ae.to] = nd
                parent[ae.to] = u
                heapq.heappush(pq, (nd, ae.to))

    if target not in dist:
        return PathResult(algorithm_used="dijkstra", path_exists=False)
    path = _reconstruct_path(parent, source, target)
    return PathResult(algorithm_used="dijkstra", path_exists=True, distance=dist[target], path=path)


def _bellman_ford_shortest_path(graph: Graph, source: str, target: str, *, undirected: bool) -> PathResult:
    ids = node_ids(graph)
    if source not in ids or target not in ids:
        return PathResult(algorithm_used="bellman_ford", path_exists=False)

    # Build edge list
    edges: list[tuple[str, str, float]] = []
    for e in graph.edges:
        w = float(e.weight if e.weight is not None else 1.0)
        edges.append((e.source, e.target, w))
        if undirected:
            edges.append((e.target, e.source, w))

    dist: dict[str, float] = {source: 0.0}
    parent: dict[str, str] = {}

    # Relax V-1 times
    for _ in range(max(0, len(ids) - 1)):
        changed = False
        for u, v, w in edges:
            if u not in dist:
                continue
            nd = dist[u] + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                parent[v] = u
                changed = True
        if not changed:
            break

    # Detect negative cycle reachable from source
    for u, v, w in edges:
        if u not in dist:
            continue
        if dist[u] + w < dist.get(v, float("inf")):
            raise NegativeCycleError("Negative cycle detected (reachable from source).")

    if target not in dist:
        return PathResult(algorithm_used="bellman_ford", path_exists=False)
    path = _reconstruct_path(parent, source, target)
    return PathResult(algorithm_used="bellman_ford", path_exists=True, distance=dist[target], path=path)


def shortest_path_info(
    graph: Graph,
    *,
    source: str,
    target: str,
    algorithm: ShortestPathAlgorithm = "auto",
    supplied_path: Optional[list[str]] = None,
) -> PathResult:
    undirected = not bool(graph.directed)

    # Auto-select algorithm
    if algorithm == "auto":
        weights = [float(e.weight if e.weight is not None else 1.0) for e in graph.edges]
        has_negative = any(w < 0 for w in weights)
        is_unweighted = all(abs(w - 1.0) < 1e-12 for w in weights) or len(weights) == 0
        if has_negative:
            algorithm = "bellman_ford"
        elif is_unweighted:
            algorithm = "bfs"
        else:
            algorithm = "dijkstra"

    if algorithm == "bfs":
        info = _bfs_shortest_path(graph, source, target, undirected=undirected)
    elif algorithm == "dijkstra":
        info = _dijkstra_shortest_path(graph, source, target, undirected=undirected)
    elif algorithm == "bellman_ford":
        info = _bellman_ford_shortest_path(graph, source, target, undirected=undirected)
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")

    # Validate supplied path (if any)
    if supplied_path is not None:
        w_lookup = edge_weight_lookup(graph, undirected=undirected)
        w = path_weight(supplied_path, w_lookup)
        is_valid = w is not None and len(supplied_path) >= 1 and supplied_path[0] == source and supplied_path[-1] == target
        is_shortest = None
        if info.path_exists and info.distance is not None and is_valid and w is not None:
            is_shortest = abs(w - info.distance) < 1e-9
        info = info.model_copy(
            update={
                "supplied_path_is_valid": is_valid,
                "supplied_path_weight": w,
                "supplied_path_is_shortest": is_shortest,
            }
        )

    return info

