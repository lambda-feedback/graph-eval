from evaluation_function.algorithms.clique import clique_number
from evaluation_function.schemas import Edge, Graph, Node


def g(nodes, edges):
    return Graph(nodes=[Node(id=n) for n in nodes], edges=[Edge(**e) for e in edges])


class TestCliqueNumber:
    def test_empty(self):
        assert clique_number(Graph(nodes=[], edges=[])) == 0

    def test_single_node(self):
        assert clique_number(g(["A"], [])) == 1

    def test_single_edge(self):
        assert clique_number(g(["A", "B"], [{"source": "A", "target": "B"}])) == 2

    def test_triangle(self):
        assert clique_number(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])) == 3

    def test_k4(self):
        nodes = ["A", "B", "C", "D"]
        edges = [{"source": a, "target": b} for i, a in enumerate(nodes) for b in nodes[i+1:]]
        assert clique_number(g(nodes, edges)) == 4

    def test_triangle_plus_pendant(self):
        assert clique_number(g(["A", "B", "C", "D"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"},
            {"source": "C", "target": "A"}, {"source": "A", "target": "D"},
        ])) == 3

    def test_no_edges(self):
        assert clique_number(g(["A", "B", "C"], [])) == 1

    def test_petersen(self):
        nodes = [f"o{i}" for i in range(5)] + [f"i{i}" for i in range(5)]
        edges = (
            [{"source": f"o{i}", "target": f"o{(i+1)%5}"} for i in range(5)] +
            [{"source": f"i{i}", "target": f"i{(i+2)%5}"} for i in range(5)] +
            [{"source": f"o{i}", "target": f"i{i}"} for i in range(5)]
        )
        assert clique_number(g(nodes, edges)) == 2
