from __future__ import annotations

from collections import deque

from evaluation_function.schemas import BipartiteResult, Graph

from .utils import build_adjacency, node_ids


def _reconstruct_odd_cycle(u: str, v: str, parent: dict[str, str], depth: dict[str, int]) -> list[str]:
    # Build paths to root
    pu = [u]
    pv = [v]
    cu, cv = u, v
    while cu in parent:
        cu = parent[cu]
        pu.append(cu)
    while cv in parent:
        cv = parent[cv]
        pv.append(cv)

    set_pu = {x: i for i, x in enumerate(pu)}
    lca = None
    j = None
    for idx, node in enumerate(pv):
        if node in set_pu:
            lca = node
            j = idx
            break

    if lca is None or j is None:
        # Fallback: just return the triangle-ish evidence
        return [u, v, u]

    i = set_pu[lca]
    path_u_to_lca = pu[: i + 1]  # u..lca
    path_v_to_lca = pv[: j + 1]  # v..lca
    path_v_to_lca.reverse()  # lca..v

    cycle = path_u_to_lca + path_v_to_lca[1:] + [u]
    return cycle


def bipartite_info(
    graph: Graph,
    *,
    return_partitions: bool = False,
    return_odd_cycle: bool = False,
) -> BipartiteResult:
    # Bipartite is typically defined for undirected graphs; we treat directed as undirected for checking.
    adj = build_adjacency(graph, undirected=True)

    color: dict[str, int] = {}
    parent: dict[str, str] = {}
    depth: dict[str, int] = {}

    for start in node_ids(graph):
        if start in color:
            continue
        q = deque([start])
        color[start] = 0
        depth[start] = 0

        while q:
            u = q.popleft()
            for ae in adj.get(u, []):
                v = ae.to
                if v not in color:
                    color[v] = 1 - color[u]
                    parent[v] = u
                    depth[v] = depth[u] + 1
                    q.append(v)
                elif color[v] == color[u]:
                    cycle = _reconstruct_odd_cycle(u, v, parent, depth) if return_odd_cycle else None
                    return BipartiteResult(is_bipartite=False, partitions=None, odd_cycle=cycle)

    partitions = None
    if return_partitions:
        left = [n for n in color.keys() if color[n] == 0]
        right = [n for n in color.keys() if color[n] == 1]
        partitions = [left, right]

    return BipartiteResult(is_bipartite=True, partitions=partitions, odd_cycle=None)

