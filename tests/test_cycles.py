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
        info = cycle_info(graph, find_all=False, return_cycles=True, return_girth=True, return_shortest_cycle=True)
        assert info.has_cycle is False
        assert info.girth is None
        assert info.shortest_cycle is None
        assert info.cycles in (None, [])

    def test_undirected_triangle_has_cycle(self):
        graph = g(
            ["A", "B", "C"],
            [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}],
            directed=False,
        )
        info = cycle_info(graph, find_all=False, return_cycles=True, return_girth=True, return_shortest_cycle=True)
        assert info.has_cycle is True
        assert info.girth == 3
        assert info.shortest_cycle is not None
        assert len(info.shortest_cycle) == 4  # closed cycle
        assert info.shortest_cycle[0] == info.shortest_cycle[-1]

    def test_directed_dag_is_acyclic(self):
        graph = g(
            ["1", "2", "3"],
            [{"source": "1", "target": "2"}, {"source": "2", "target": "3"}, {"source": "1", "target": "3"}],
            directed=True,
        )
        info = cycle_info(graph, find_all=False, return_cycles=True, return_girth=True, return_shortest_cycle=True)
        assert info.has_cycle is False
        assert info.girth is None
        assert info.shortest_cycle is None

    def test_directed_cycle_detected(self):
        graph = g(
            ["A", "B", "C"],
            [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}],
            directed=True,
        )
        info = cycle_info(graph, find_all=False, return_cycles=True, return_girth=True, return_shortest_cycle=True)
        assert info.has_cycle is True
        assert info.girth == 3
        assert info.shortest_cycle is not None
        assert info.shortest_cycle[0] == info.shortest_cycle[-1]

    def test_directed_self_loop_is_cycle_length_1(self):
        graph = g(["A"], [{"source": "A", "target": "A"}], directed=True)
        info = cycle_info(graph, find_all=False, return_cycles=True, return_girth=True, return_shortest_cycle=True)
        assert info.has_cycle is True
        assert info.girth == 1
        assert info.shortest_cycle == ["A", "A"]


class TestAllCycles:
    def test_find_all_cycles_undirected_small_graph(self):
        # Square with a diagonal -> 2 triangles + 1 square
        graph = g(
            ["A", "B", "C", "D"],
            [
                {"source": "A", "target": "B"},
                {"source": "B", "target": "C"},
                {"source": "C", "target": "D"},
                {"source": "D", "target": "A"},
                {"source": "A", "target": "C"},
            ],
            directed=False,
        )
        info = cycle_info(
            graph,
            find_all=True,
            min_length=3,
            max_length=None,
            max_nodes=15,
            max_cycles=100,
            return_cycles=True,
            return_girth=True,
            return_shortest_cycle=True,
        )
        assert info.has_cycle is True
        assert info.cycles is not None
        lengths = sorted({len(c) - 1 for c in info.cycles})  # edge-counts
        assert lengths == [3, 4]
        assert sum(1 for c in info.cycles if (len(c) - 1) == 3) == 2
        assert sum(1 for c in info.cycles if (len(c) - 1) == 4) == 1

    def test_find_all_cycles_respects_max_length(self):
        graph = g(
            ["A", "B", "C", "D"],
            [
                {"source": "A", "target": "B"},
                {"source": "B", "target": "C"},
                {"source": "C", "target": "D"},
                {"source": "D", "target": "A"},
                {"source": "A", "target": "C"},
            ],
            directed=False,
        )
        info = cycle_info(
            graph,
            find_all=True,
            min_length=3,
            max_length=3,
            max_nodes=15,
            max_cycles=100,
            return_cycles=True,
            return_girth=False,
            return_shortest_cycle=False,
        )
        assert info.cycles is not None
        assert all((len(c) - 1) == 3 for c in info.cycles)

    def test_find_all_cycles_guard_max_nodes(self):
        # Create a simple big cycle with 16 nodes (guard should prevent enumeration)
        nodes = [str(i) for i in range(16)]
        edges = [{"source": str(i), "target": str((i + 1) % 16)} for i in range(16)]
        graph = g(nodes, edges, directed=False)
        info = cycle_info(
            graph,
            find_all=True,
            max_nodes=15,
            max_cycles=100,
            return_cycles=True,
            return_girth=True,
            return_shortest_cycle=True,
        )
        assert info.has_cycle is True
        assert info.cycles == []  # enumeration skipped
        assert info.girth == 16


class TestNegativeCycle:
    def test_negative_cycle_directed_detected(self):
        graph = g(
            ["A", "B"],
            [{"source": "A", "target": "B", "weight": 1}, {"source": "B", "target": "A", "weight": -2}],
            directed=True,
        )
        info = cycle_info(
            graph,
            detect_negative_cycle=True,
            return_negative_cycle=True,
            return_girth=False,
            return_shortest_cycle=False,
            return_cycles=False,
        )
        assert info.has_negative_cycle is True
        assert info.negative_cycle is not None
        assert info.negative_cycle[0] == info.negative_cycle[-1]

    def test_negative_cycle_undirected_negative_edge_detected(self):
        # Under our undirected-as-bidirectional model, a single negative edge implies a negative 2-cycle.
        graph = g(
            ["A", "B"],
            [{"source": "A", "target": "B", "weight": -1}],
            directed=False,
        )
        info = cycle_info(
            graph,
            detect_negative_cycle=True,
            return_negative_cycle=True,
            return_girth=False,
            return_shortest_cycle=False,
            return_cycles=False,
        )
        assert info.has_negative_cycle is True
        assert info.negative_cycle is not None

    def test_no_negative_cycle(self):
        graph = g(
            ["A", "B", "C"],
            [
                {"source": "A", "target": "B", "weight": 1},
                {"source": "B", "target": "C", "weight": 1},
                {"source": "C", "target": "A", "weight": 1},
            ],
            directed=True,
        )
        info = cycle_info(
            graph,
            detect_negative_cycle=True,
            return_negative_cycle=True,
            return_girth=False,
            return_shortest_cycle=False,
            return_cycles=False,
        )
        assert info.has_negative_cycle is False
        assert info.negative_cycle is None

