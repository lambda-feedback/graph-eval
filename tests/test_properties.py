from evaluation_function.algorithms.properties import (
    is_tree, is_forest, is_dag, is_eulerian, is_semi_eulerian,
    is_regular, is_complete, degree_sequence, is_subgraph,
)
from evaluation_function.schemas import Edge, Graph, Node


def g(nodes, edges, *, directed=False):
    return Graph(nodes=[Node(id=n) for n in nodes], edges=[Edge(**e) for e in edges], directed=directed)


# ── is_tree ──────────────────────────────────────────────────────────────

class TestIsTree:
    def test_single_node(self):
        assert is_tree(g(["A"], [])) is True

    def test_path_is_tree(self):
        assert is_tree(g(["A", "B", "C"], [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}])) is True

    def test_triangle_not_tree(self):
        assert is_tree(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])) is False

    def test_disconnected_not_tree(self):
        assert is_tree(g(["A", "B"], [])) is False


# ── is_forest ────────────────────────────────────────────────────────────

class TestIsForest:
    def test_disconnected_acyclic(self):
        assert is_forest(g(["A", "B", "C"], [{"source": "A", "target": "B"}])) is True

    def test_triangle_not_forest(self):
        assert is_forest(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])) is False

    def test_empty_is_forest(self):
        assert is_forest(Graph(nodes=[], edges=[])) is True


# ── is_dag ───────────────────────────────────────────────────────────────

class TestIsDAG:
    def test_dag(self):
        assert is_dag(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "A", "target": "C"}
        ], directed=True)) is True

    def test_directed_cycle_not_dag(self):
        assert is_dag(g(["A", "B"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "A"}
        ], directed=True)) is False

    def test_undirected_never_dag(self):
        assert is_dag(g(["A", "B"], [{"source": "A", "target": "B"}])) is False


# ── degree_sequence ──────────────────────────────────────────────────────

class TestDegreeSequence:
    def test_triangle(self):
        assert degree_sequence(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])) == [2, 2, 2]

    def test_star(self):
        assert degree_sequence(g(["C", "L1", "L2", "L3"], [
            {"source": "C", "target": "L1"}, {"source": "C", "target": "L2"}, {"source": "C", "target": "L3"}
        ])) == [3, 1, 1, 1]

    def test_isolated(self):
        assert degree_sequence(g(["A", "B"], [])) == [0, 0]


# ── is_regular ───────────────────────────────────────────────────────────

class TestIsRegular:
    def test_triangle_regular(self):
        assert is_regular(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])) is True

    def test_star_not_regular(self):
        assert is_regular(g(["C", "L1", "L2"], [
            {"source": "C", "target": "L1"}, {"source": "C", "target": "L2"}
        ])) is False

    def test_empty_regular(self):
        assert is_regular(Graph(nodes=[], edges=[])) is True


# ── is_complete ──────────────────────────────────────────────────────────

class TestIsComplete:
    def test_k3(self):
        assert is_complete(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])) is True

    def test_missing_edge(self):
        assert is_complete(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}
        ])) is False

    def test_single_node(self):
        assert is_complete(g(["A"], [])) is True


# ── is_eulerian ──────────────────────────────────────────────────────────

class TestIsEulerian:
    def test_triangle_eulerian(self):
        assert is_eulerian(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])) is True

    def test_path_not_eulerian(self):
        assert is_eulerian(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}
        ])) is False

    def test_disconnected_not_eulerian(self):
        assert is_eulerian(g(["A", "B", "C", "D"], [
            {"source": "A", "target": "B"}, {"source": "C", "target": "D"}
        ])) is False

    def test_directed_eulerian(self):
        assert is_eulerian(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ], directed=True)) is True

    def test_directed_not_eulerian(self):
        assert is_eulerian(g(["A", "B"], [
            {"source": "A", "target": "B"}
        ], directed=True)) is False


# ── is_semi_eulerian ────────────────────────────────────────────────────

class TestIsSemiEulerian:
    def test_path_semi_eulerian(self):
        assert is_semi_eulerian(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}
        ])) is True

    def test_triangle_semi_eulerian(self):
        # Euler circuit is also an Euler path
        assert is_semi_eulerian(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])) is True

    def test_four_odd_vertices_not_semi(self):
        assert is_semi_eulerian(g(["A", "B", "C", "D"], [
            {"source": "A", "target": "B"}, {"source": "C", "target": "D"}
        ])) is False

    def test_directed_semi_eulerian(self):
        assert is_semi_eulerian(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}
        ], directed=True)) is True


# ── is_subgraph ──────────────────────────────────────────────────────────

class TestIsSubgraph:
    def test_subgraph(self):
        parent = g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}
        ])
        sub = g(["A", "B"], [{"source": "A", "target": "B"}])
        assert is_subgraph(sub, parent) is True

    def test_not_subgraph_extra_edge(self):
        parent = g(["A", "B", "C"], [{"source": "A", "target": "B"}])
        sub = g(["A", "B"], [{"source": "A", "target": "B"}, {"source": "B", "target": "A"}])
        # In undirected parent, B-A exists implicitly
        assert is_subgraph(sub, parent) is True

    def test_not_subgraph_extra_node(self):
        parent = g(["A", "B"], [{"source": "A", "target": "B"}])
        sub = g(["A", "B", "C"], [{"source": "A", "target": "B"}])
        assert is_subgraph(sub, parent) is False

    def test_not_subgraph_missing_edge(self):
        parent = g(["A", "B", "C"], [{"source": "A", "target": "B"}])
        sub = g(["A", "C"], [{"source": "A", "target": "C"}])
        assert is_subgraph(sub, parent) is False

    def test_directed_subgraph(self):
        parent = g(["A", "B"], [{"source": "A", "target": "B"}], directed=True)
        sub = g(["A", "B"], [{"source": "B", "target": "A"}], directed=True)
        assert is_subgraph(sub, parent) is False
