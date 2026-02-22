import pytest

from evaluation_function.algorithms.cycles import cycle_info
from evaluation_function.schemas import Edge, Graph, Node


def g(nodes, edges, *, directed=False):
    return Graph(nodes=[Node(id=n) for n in nodes], edges=[Edge(**e) for e in edges], directed=directed)


class TestCycleDetection:
    def test_undirected_tree_is_acyclic(self):
        graph = g(
            ["A", "B", "C", "D"],
            [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "D"}],
            directed=False,
        )
        info = cycle_info(graph)
        assert info.has_cycle is False
        assert info.cycle is None

    def test_undirected_triangle_has_cycle(self):
        graph = g(
            ["A", "B", "C"],
            [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}],
            directed=False,
        )
        info = cycle_info(graph)
        assert info.has_cycle is True
        assert info.cycle is not None

    def test_directed_dag_is_acyclic(self):
        graph = g(
            ["1", "2", "3"],
            [{"source": "1", "target": "2"}, {"source": "2", "target": "3"}, {"source": "1", "target": "3"}],
            directed=True,
        )
        info = cycle_info(graph)
        assert info.has_cycle is False

    def test_directed_cycle_detected(self):
        graph = g(
            ["A", "B", "C"],
            [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}],
            directed=True,
        )
        info = cycle_info(graph)
        assert info.has_cycle is True
        assert info.cycle is not None

    def test_directed_self_loop_is_cycle(self):
        graph = g(["A"], [{"source": "A", "target": "A"}], directed=True)
        info = cycle_info(graph)
        assert info.has_cycle is True

    def test_single_node_no_cycle(self):
        graph = g(["A"], [], directed=False)
        info = cycle_info(graph)
        assert info.has_cycle is False

    def test_empty_graph_no_cycle(self):
        graph = Graph(nodes=[], edges=[])
        info = cycle_info(graph)
        assert info.has_cycle is False

    def test_disconnected_with_cycle(self):
        graph = g(
            ["A", "B", "C", "X", "Y"],
            [
                {"source": "A", "target": "B"},
                {"source": "B", "target": "C"},
                {"source": "C", "target": "A"},
                {"source": "X", "target": "Y"},
            ],
            directed=False,
        )
        info = cycle_info(graph)
        assert info.has_cycle is True
