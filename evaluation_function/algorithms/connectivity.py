from __future__ import annotations

from collections import deque
from typing import Literal, Optional

from evaluation_function.schemas import ConnectivityResult, Graph

from .utils import build_adjacency, build_reverse_adjacency, node_ids


ConnectivityType = Literal["connected", "strongly_connected", "weakly_connected"]


def _components_undirected(graph: Graph) -> list[list[str]]:
    adj = build_adjacency(graph, undirected=True)
    seen: set[str] = set()
    comps: list[list[str]] = []
    for start in node_ids(graph):
        if start in seen:
            continue
        q = deque([start])
        seen.add(start)
        comp: list[str] = []
        while q:
            u = q.popleft()
            comp.append(u)
            for ae in adj.get(u, []):
                if ae.to not in seen:
                    seen.add(ae.to)
                    q.append(ae.to)
        comps.append(comp)
    return comps


def _is_strongly_connected(graph: Graph) -> bool:
    ids = node_ids(graph)
    if len(ids) <= 1:
        return True

    adj = build_adjacency(graph, undirected=False)
    radj = build_reverse_adjacency(graph)

    def dfs(start: str, adjacency: dict[str, list]) -> set[str]:
        stack = [start]
        seen: set[str] = set()
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            for ae in adjacency.get(u, []):
                if ae.to not in seen:
                    stack.append(ae.to)
        return seen

    s = ids[0]
    if len(dfs(s, adj)) != len(ids):
        return False
    if len(dfs(s, radj)) != len(ids):
        return False
    return True


def connectivity_info(
    graph: Graph,
    *,
    connectivity_type: ConnectivityType = "connected",
    return_components: bool = False,
) -> ConnectivityResult:
    ids = node_ids(graph)
    if len(ids) <= 1:
        comps = [ids]
        return ConnectivityResult(
            is_connected=True,
            num_components=len(comps),
            components=comps if return_components else None,
            connectivity_type=connectivity_type,
            largest_component_size=len(ids),
        )

    if connectivity_type == "strongly_connected":
        is_conn = _is_strongly_connected(graph)
        # Components for SCCs are out-of-scope for this ticket.
        return ConnectivityResult(
            is_connected=is_conn,
            num_components=1 if is_conn else 2,
            components=None,
            connectivity_type=connectivity_type,
            largest_component_size=len(ids) if is_conn else None,
        )

    if connectivity_type == "weakly_connected":
        comps = _components_undirected(graph)
        return ConnectivityResult(
            is_connected=len(comps) == 1,
            num_components=len(comps),
            components=comps if return_components else None,
            connectivity_type=connectivity_type,
            largest_component_size=max((len(c) for c in comps), default=0),
        )

    # Default: undirected connectivity.
    comps = _components_undirected(graph)
    return ConnectivityResult(
        is_connected=len(comps) == 1,
        num_components=len(comps),
        components=comps if return_components else None,
        connectivity_type="connected",
        largest_component_size=max((len(c) for c in comps), default=0),
    )

