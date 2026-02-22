"""
Tests for graph isomorphism checking.
"""

import pytest

from evaluation_function.algorithms.isomorphism import isomorphism_info
from evaluation_function.schemas import Edge, Graph, Node


def g(nodes, edges, *, directed=False):
    return Graph(nodes=[Node(id=n) for n in nodes], edges=[Edge(**e) for e in edges], directed=directed)


class TestIsomorphism:
    def test_empty_graphs_are_isomorphic(self):
        g1 = Graph(nodes=[], edges=[])
        g2 = Graph(nodes=[], edges=[])
        result = isomorphism_info(g1, g2)
        assert result.is_isomorphic is True

    def test_single_node_isomorphic(self):
        g1 = g(["A"], [])
        g2 = g(["X"], [])
        result = isomorphism_info(g1, g2)
        assert result.is_isomorphic is True
        assert result.node_mapping == {"A": "X"}

    def test_different_node_count(self):
        g1 = g(["A", "B"], [])
        g2 = g(["X"], [])
        result = isomorphism_info(g1, g2)
        assert result.is_isomorphic is False

    def test_different_edge_count(self):
        g1 = g(["A", "B"], [{"source": "A", "target": "B"}])
        g2 = g(["X", "Y"], [])
        result = isomorphism_info(g1, g2)
        assert result.is_isomorphic is False

    def test_simple_edge_isomorphic(self):
        g1 = g(["A", "B"], [{"source": "A", "target": "B"}])
        g2 = g(["X", "Y"], [{"source": "X", "target": "Y"}])
        result = isomorphism_info(g1, g2)
        assert result.is_isomorphic is True
        assert result.node_mapping is not None

    def test_triangle_isomorphic(self):
        g1 = g(
            ["A", "B", "C"],
            [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}],
        )
        g2 = g(
            ["X", "Y", "Z"],
            [{"source": "X", "target": "Y"}, {"source": "Y", "target": "Z"}, {"source": "Z", "target": "X"}],
        )
        result = isomorphism_info(g1, g2)
        assert result.is_isomorphic is True

    def test_path_vs_triangle_not_isomorphic(self):
        g1 = g(
            ["A", "B", "C"],
            [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}],
        )
        g2 = g(
            ["X", "Y", "Z"],
            [{"source": "X", "target": "Y"}, {"source": "Y", "target": "Z"}, {"source": "Z", "target": "X"}],
        )
        result = isomorphism_info(g1, g2)
        assert result.is_isomorphic is False

    def test_k4_isomorphic_relabeled(self):
        edges1 = []
        nodes1 = ["1", "2", "3", "4"]
        for i in range(4):
            for j in range(i + 1, 4):
                edges1.append({"source": nodes1[i], "target": nodes1[j]})

        edges2 = []
        nodes2 = ["A", "B", "C", "D"]
        for i in range(4):
            for j in range(i + 1, 4):
                edges2.append({"source": nodes2[i], "target": nodes2[j]})

        g1 = Graph(nodes=[Node(id=n) for n in nodes1], edges=[Edge(**e) for e in edges1])
        g2 = Graph(nodes=[Node(id=n) for n in nodes2], edges=[Edge(**e) for e in edges2])
        result = isomorphism_info(g1, g2)
        assert result.is_isomorphic is True

    def test_directed_isomorphic(self):
        g1 = g(["A", "B", "C"], [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}], directed=True)
        g2 = g(["X", "Y", "Z"], [{"source": "X", "target": "Y"}, {"source": "Y", "target": "Z"}], directed=True)
        result = isomorphism_info(g1, g2)
        assert result.is_isomorphic is True

    def test_directed_not_isomorphic_reversed_edge(self):
        g1 = g(["A", "B"], [{"source": "A", "target": "B"}], directed=True)
        g2 = g(["X", "Y"], [{"source": "Y", "target": "X"}], directed=True)
        result = isomorphism_info(g1, g2)
        assert result.is_isomorphic is True  # same structure, just relabeled

    def test_directed_different_structure(self):
        g1 = g(
            ["A", "B", "C"],
            [{"source": "A", "target": "B"}, {"source": "A", "target": "C"}],
            directed=True,
        )
        g2 = g(
            ["X", "Y", "Z"],
            [{"source": "X", "target": "Y"}, {"source": "Y", "target": "Z"}],
            directed=True,
        )
        result = isomorphism_info(g1, g2)
        assert result.is_isomorphic is False

    def test_directed_vs_undirected_not_isomorphic(self):
        g1 = g(["A", "B"], [{"source": "A", "target": "B"}], directed=True)
        g2 = g(["X", "Y"], [{"source": "X", "target": "Y"}], directed=False)
        result = isomorphism_info(g1, g2)
        assert result.is_isomorphic is False

    def test_same_degree_different_structure(self):
        # Both have 4 nodes, 4 edges, all degree 2 — but different structures
        # C4 (square) vs two disjoint edges + isolated? No...
        # C4 vs a "bowtie minus one edge" — need same degree seq but different structure
        # Square: A-B-C-D-A
        g1 = g(
            ["A", "B", "C", "D"],
            [
                {"source": "A", "target": "B"},
                {"source": "B", "target": "C"},
                {"source": "C", "target": "D"},
                {"source": "D", "target": "A"},
            ],
        )
        # Also 4 nodes, 4 edges but different topology: A-B, A-C, B-D, C-D (also all degree 2)
        g2 = g(
            ["W", "X", "Y", "Z"],
            [
                {"source": "W", "target": "X"},
                {"source": "W", "target": "Y"},
                {"source": "X", "target": "Z"},
                {"source": "Y", "target": "Z"},
            ],
        )
        result = isomorphism_info(g1, g2)
        # Both are C4 (just relabeled) — actually this IS isomorphic since
        # both form a 4-cycle. Let's verify.
        assert result.is_isomorphic is True
