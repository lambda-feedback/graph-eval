"""
Graph Isomorphism — check if two graphs are isomorphic.

Uses degree-sequence pruning followed by backtracking to find a valid
node mapping between the two graphs.
"""

from __future__ import annotations

from itertools import permutations
from typing import Optional

from evaluation_function.schemas import Graph, IsomorphismResult


def _edge_set(graph: Graph) -> set[tuple[str, str]]:
    """Return the set of edges. For undirected graphs, store both directions."""
    edges: set[tuple[str, str]] = set()
    for e in graph.edges:
        edges.add((e.source, e.target))
        if not graph.directed:
            edges.add((e.target, e.source))
    return edges


def _degree_sequence(graph: Graph) -> dict[str, int]:
    """Compute the degree of each node."""
    deg: dict[str, int] = {n.id: 0 for n in graph.nodes}
    for e in graph.edges:
        deg[e.source] = deg.get(e.source, 0) + 1
        if not graph.directed:
            deg[e.target] = deg.get(e.target, 0) + 1
        else:
            # For directed: count out-degree; we'll also track in-degree
            deg[e.target] = deg.get(e.target, 0) + 1
    return deg


def _in_out_degrees(graph: Graph) -> dict[str, tuple[int, int]]:
    """For directed graphs, compute (in_degree, out_degree) per node."""
    in_deg: dict[str, int] = {n.id: 0 for n in graph.nodes}
    out_deg: dict[str, int] = {n.id: 0 for n in graph.nodes}
    for e in graph.edges:
        out_deg[e.source] = out_deg.get(e.source, 0) + 1
        in_deg[e.target] = in_deg.get(e.target, 0) + 1
    return {nid: (in_deg[nid], out_deg[nid]) for nid in in_deg}


def isomorphism_info(graph1: Graph, graph2: Graph) -> IsomorphismResult:
    """
    Check whether two graphs are isomorphic.

    Quick checks on node/edge counts and degree sequences are done first.
    Then a backtracking search attempts to find a valid mapping.
    """
    nodes1 = [n.id for n in graph1.nodes]
    nodes2 = [n.id for n in graph2.nodes]

    # Quick checks
    if len(nodes1) != len(nodes2):
        return IsomorphismResult(is_isomorphic=False)
    if len(graph1.edges) != len(graph2.edges):
        return IsomorphismResult(is_isomorphic=False)
    if bool(graph1.directed) != bool(graph2.directed):
        return IsomorphismResult(is_isomorphic=False)

    n = len(nodes1)
    if n == 0:
        return IsomorphismResult(is_isomorphic=True, node_mapping={})

    directed = bool(graph1.directed)
    edges1 = _edge_set(graph1)
    edges2 = _edge_set(graph2)

    # Degree-based pruning
    if directed:
        io1 = _in_out_degrees(graph1)
        io2 = _in_out_degrees(graph2)
        sig1 = sorted(io1.values())
        sig2 = sorted(io2.values())
        if sig1 != sig2:
            return IsomorphismResult(is_isomorphic=False)
        # Group nodes by (in, out) degree
        groups1: dict[tuple[int, int], list[str]] = {}
        for nid, sig in io1.items():
            groups1.setdefault(sig, []).append(nid)
        groups2: dict[tuple[int, int], list[str]] = {}
        for nid, sig in io2.items():
            groups2.setdefault(sig, []).append(nid)
    else:
        deg1 = _degree_sequence(graph1)
        deg2 = _degree_sequence(graph2)
        sig1_u = sorted(deg1.values())
        sig2_u = sorted(deg2.values())
        if sig1_u != sig2_u:
            return IsomorphismResult(is_isomorphic=False)
        groups1 = {}
        for nid, d in deg1.items():
            groups1.setdefault((d,), []).append(nid)
        groups2 = {}
        for nid, d in deg2.items():
            groups2.setdefault((d,), []).append(nid)

    # Build ordered groups for backtracking
    keys = sorted(groups1.keys())
    ordered_nodes1: list[str] = []
    candidate_lists: list[list[str]] = []
    for k in keys:
        g1 = sorted(groups1[k])
        g2 = sorted(groups2[k])
        if len(g1) != len(g2):
            return IsomorphismResult(is_isomorphic=False)
        ordered_nodes1.extend(g1)
        candidate_lists.append(g2)

    # For small graphs, try all permutations within each group
    # Build the backtracking over groups
    mapping: dict[str, str] = {}
    used: set[str] = set()

    def _check_mapping_valid() -> bool:
        for u, v in edges1:
            mu = mapping.get(u)
            mv = mapping.get(v)
            if mu is not None and mv is not None:
                if (mu, mv) not in edges2:
                    return False
        return True

    def _backtrack_groups(group_idx: int) -> Optional[dict[str, str]]:
        if group_idx == len(keys):
            # Full mapping — verify all edges
            for u, v in edges1:
                if (mapping[u], mapping[v]) not in edges2:
                    return None
            return dict(mapping)

        k = keys[group_idx]
        g1 = groups1[k]
        g2_available = [x for x in groups2[k] if x not in used]

        if len(g1) != len(g2_available):
            return None

        for perm in permutations(g2_available):
            # Assign this permutation
            for i, nid in enumerate(g1):
                mapping[nid] = perm[i]
                used.add(perm[i])

            # Early pruning: check edges involving assigned nodes
            valid = True
            for u, v in edges1:
                mu = mapping.get(u)
                mv = mapping.get(v)
                if mu is not None and mv is not None:
                    if (mu, mv) not in edges2:
                        valid = False
                        break

            if valid:
                result = _backtrack_groups(group_idx + 1)
                if result is not None:
                    return result

            # Undo
            for i, nid in enumerate(g1):
                used.discard(perm[i])
                del mapping[nid]

        return None

    result = _backtrack_groups(0)
    if result is not None:
        return IsomorphismResult(is_isomorphic=True, node_mapping=result)
    return IsomorphismResult(is_isomorphic=False)
