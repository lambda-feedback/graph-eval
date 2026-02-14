import pytest

from evaluation_function.algorithms.bipartite import bipartite_info
from evaluation_function.algorithms.connectivity import connectivity_info
from evaluation_function.algorithms.shortest_path import NegativeCycleError, shortest_path_info
from evaluation_function.schemas import Edge, Graph, Node


def g(nodes, edges, *, directed=False):
    return Graph(nodes=[Node(id=n) for n in nodes], edges=[Edge(**e) for e in edges], directed=directed)


class TestConnectivity:
    def test_empty_graph_is_connected(self):
        graph = Graph(nodes=[], edges=[], directed=False)
        info = connectivity_info(graph)
        assert info.is_connected is True

    def test_undirected_disconnected(self):
        graph = g(["A", "B"], [], directed=False)
        info = connectivity_info(graph, return_components=True)
        assert info.is_connected is False
        assert sorted([sorted(c) for c in info.components]) == [["A"], ["B"]]

    def test_directed_strongly_connected(self):
        graph = g(["A", "B"], [{"source": "A", "target": "B"}, {"source": "B", "target": "A"}], directed=True)
        info = connectivity_info(graph, connectivity_type="strongly_connected")
        assert info.is_connected is True

    def test_directed_weakly_connected(self):
        graph = g(["A", "B"], [{"source": "A", "target": "B"}], directed=True)
        info = connectivity_info(graph, connectivity_type="weakly_connected")
        assert info.is_connected is True

    def test_directed_not_strongly_connected(self):
        graph = g(["A", "B"], [{"source": "A", "target": "B"}], directed=True)
        info = connectivity_info(graph, connectivity_type="strongly_connected")
        assert info.is_connected is False


class TestShortestPath:
    def test_unweighted_bfs(self):
        graph = g(["A", "B", "C"], [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}], directed=False)
        info = shortest_path_info(graph, source="A", target="C", algorithm="auto")
        assert info.path_exists is True
        assert info.algorithm_used == "bfs"
        assert info.distance == 2.0
        assert info.path == ["A", "B", "C"]

    def test_weighted_dijkstra(self):
        graph = g(
            ["A", "B", "C"],
            [
                {"source": "A", "target": "B", "weight": 2},
                {"source": "B", "target": "C", "weight": 2},
                {"source": "A", "target": "C", "weight": 10},
            ],
            directed=False,
        )
        info = shortest_path_info(graph, source="A", target="C", algorithm="auto")
        assert info.algorithm_used == "dijkstra"
        assert info.distance == 4.0
        assert info.path == ["A", "B", "C"]

    def test_negative_weight_bellman_ford(self):
        graph = g(
            ["A", "B", "C"],
            [
                {"source": "A", "target": "B", "weight": -1},
                {"source": "B", "target": "C", "weight": 2},
                {"source": "A", "target": "C", "weight": 5},
            ],
            directed=True,
        )
        info = shortest_path_info(graph, source="A", target="C", algorithm="auto")
        assert info.algorithm_used == "bellman_ford"
        assert info.distance == 1.0
        assert info.path == ["A", "B", "C"]

    def test_negative_cycle_raises(self):
        graph = g(
            ["A", "B"],
            [{"source": "A", "target": "B", "weight": 1}, {"source": "B", "target": "A", "weight": -2}],
            directed=True,
        )
        with pytest.raises(NegativeCycleError):
            shortest_path_info(graph, source="A", target="B", algorithm="auto")

    def test_supplied_path_validation(self):
        graph = g(["A", "B", "C"], [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}], directed=False)
        info = shortest_path_info(graph, source="A", target="C", algorithm="auto", supplied_path=["A", "B", "C"])
        assert info.supplied_path_is_valid is True
        assert info.supplied_path_is_shortest is True


class TestBipartite:
    def test_bipartite_square(self):
        graph = g(
            ["A", "B", "C", "D"],
            [
                {"source": "A", "target": "B"},
                {"source": "B", "target": "C"},
                {"source": "C", "target": "D"},
                {"source": "D", "target": "A"},
            ],
            directed=False,
        )
        info = bipartite_info(graph, return_partitions=True)
        assert info.is_bipartite is True
        assert info.partitions is not None

    def test_not_bipartite_triangle(self):
        graph = g(
            ["A", "B", "C"],
            [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}],
            directed=False,
        )
        info = bipartite_info(graph, return_odd_cycle=True)
        assert info.is_bipartite is False
        assert info.odd_cycle is not None
        assert len(info.odd_cycle) >= 3

