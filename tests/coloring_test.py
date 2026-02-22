"""
Tests for graph n-coloring.
"""

import pytest

from evaluation_function.schemas.graph import Graph, Node, Edge
from evaluation_function.algorithms.coloring import is_n_colorable


@pytest.fixture
def empty_graph():
    return Graph(nodes=[], edges=[])


@pytest.fixture
def single_vertex():
    return Graph(nodes=[Node(id="A")], edges=[])


@pytest.fixture
def two_edge():
    return Graph(nodes=[Node(id="A"), Node(id="B")], edges=[Edge(source="A", target="B")])


@pytest.fixture
def triangle():
    return Graph(
        nodes=[Node(id="A"), Node(id="B"), Node(id="C")],
        edges=[Edge(source="A", target="B"), Edge(source="B", target="C"), Edge(source="A", target="C")],
    )


@pytest.fixture
def k4():
    return Graph(
        nodes=[Node(id="A"), Node(id="B"), Node(id="C"), Node(id="D")],
        edges=[
            Edge(source="A", target="B"),
            Edge(source="A", target="C"),
            Edge(source="A", target="D"),
            Edge(source="B", target="C"),
            Edge(source="B", target="D"),
            Edge(source="C", target="D"),
        ],
    )


@pytest.fixture
def bipartite_graph():
    return Graph(
        nodes=[Node(id="A"), Node(id="B"), Node(id="X"), Node(id="Y")],
        edges=[Edge(source="A", target="X"), Edge(source="A", target="Y"), Edge(source="B", target="X")],
    )


@pytest.fixture
def cycle_c5():
    return Graph(
        nodes=[Node(id=str(i)) for i in range(5)],
        edges=[Edge(source=str(i), target=str((i + 1) % 5)) for i in range(5)],
    )


class TestIsNColorable:
    def test_empty_graph_any_k(self, empty_graph):
        result = is_n_colorable(empty_graph, 1)
        assert result.is_colorable is True

    def test_single_vertex_1_color(self, single_vertex):
        result = is_n_colorable(single_vertex, 1)
        assert result.is_colorable is True
        assert result.coloring == {"A": 0}

    def test_edge_needs_2_colors(self, two_edge):
        assert is_n_colorable(two_edge, 1).is_colorable is False
        result = is_n_colorable(two_edge, 2)
        assert result.is_colorable is True
        assert result.coloring["A"] != result.coloring["B"]

    def test_triangle_needs_3_colors(self, triangle):
        assert is_n_colorable(triangle, 2).is_colorable is False
        result = is_n_colorable(triangle, 3)
        assert result.is_colorable is True

    def test_k4_needs_4_colors(self, k4):
        assert is_n_colorable(k4, 3).is_colorable is False
        result = is_n_colorable(k4, 4)
        assert result.is_colorable is True

    def test_bipartite_is_2_colorable(self, bipartite_graph):
        result = is_n_colorable(bipartite_graph, 2)
        assert result.is_colorable is True

    def test_c5_needs_3_colors(self, cycle_c5):
        assert is_n_colorable(cycle_c5, 2).is_colorable is False
        result = is_n_colorable(cycle_c5, 3)
        assert result.is_colorable is True

    def test_zero_colors_not_colorable(self, single_vertex):
        result = is_n_colorable(single_vertex, 0)
        assert result.is_colorable is False

    def test_more_colors_than_needed(self, triangle):
        result = is_n_colorable(triangle, 10)
        assert result.is_colorable is True
        assert len(set(result.coloring.values())) <= 10

    def test_disconnected_graph(self):
        graph = Graph(
            nodes=[Node(id="A"), Node(id="B"), Node(id="C"), Node(id="X"), Node(id="Y")],
            edges=[
                Edge(source="A", target="B"),
                Edge(source="B", target="C"),
                Edge(source="A", target="C"),
                Edge(source="X", target="Y"),
            ],
        )
        assert is_n_colorable(graph, 2).is_colorable is False
        result = is_n_colorable(graph, 3)
        assert result.is_colorable is True
