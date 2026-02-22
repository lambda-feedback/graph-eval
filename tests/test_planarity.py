from evaluation_function.algorithms.planarity import is_planar
from evaluation_function.schemas import Edge, Graph, Node


def g(nodes, edges):
    return Graph(nodes=[Node(id=n) for n in nodes], edges=[Edge(**e) for e in edges])


class TestPlanarity:
    def test_empty(self):
        assert is_planar(Graph(nodes=[], edges=[])) is True

    def test_single_node(self):
        assert is_planar(g(["A"], [])) is True

    def test_k4_planar(self):
        nodes = ["A", "B", "C", "D"]
        edges = [{"source": a, "target": b} for i, a in enumerate(nodes) for b in nodes[i+1:]]
        assert is_planar(g(nodes, edges)) is True

    def test_k5_not_planar(self):
        nodes = [str(i) for i in range(5)]
        edges = [{"source": a, "target": b} for i, a in enumerate(nodes) for b in nodes[i+1:]]
        assert is_planar(g(nodes, edges)) is False

    def test_k33_not_planar(self):
        left = ["A1", "A2", "A3"]
        right = ["B1", "B2", "B3"]
        edges = [{"source": a, "target": b} for a in left for b in right]
        assert is_planar(g(left + right, edges)) is False

    def test_tree_planar(self):
        assert is_planar(g(
            ["R", "A", "B", "C", "D"],
            [{"source": "R", "target": "A"}, {"source": "R", "target": "B"},
             {"source": "A", "target": "C"}, {"source": "A", "target": "D"}],
        )) is True

    def test_cycle_planar(self):
        n = 6
        nodes = [str(i) for i in range(n)]
        edges = [{"source": str(i), "target": str((i+1) % n)} for i in range(n)]
        assert is_planar(g(nodes, edges)) is True

    def test_petersen_not_planar(self):
        nodes = [f"o{i}" for i in range(5)] + [f"i{i}" for i in range(5)]
        edges = (
            [{"source": f"o{i}", "target": f"o{(i+1)%5}"} for i in range(5)] +
            [{"source": f"i{i}", "target": f"i{(i+2)%5}"} for i in range(5)] +
            [{"source": f"o{i}", "target": f"i{i}"} for i in range(5)]
        )
        assert is_planar(g(nodes, edges)) is False

    def test_k5_edge_bound_rejects(self):
        # K5 has 10 edges, 3*5-6=9 → rejected by edge bound
        nodes = [str(i) for i in range(5)]
        edges = [{"source": a, "target": b} for i, a in enumerate(nodes) for b in nodes[i+1:]]
        assert is_planar(g(nodes, edges)) is False
