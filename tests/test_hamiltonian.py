from evaluation_function.algorithms.hamiltonian import has_hamiltonian_path, has_hamiltonian_cycle
from evaluation_function.schemas import Edge, Graph, Node


def g(nodes, edges, *, directed=False):
    return Graph(nodes=[Node(id=n) for n in nodes], edges=[Edge(**e) for e in edges], directed=directed)


class TestHamiltonianPath:
    def test_single_node(self):
        assert has_hamiltonian_path(g(["A"], [])) is True

    def test_path_graph(self):
        assert has_hamiltonian_path(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}
        ])) is True

    def test_disconnected_no_path(self):
        assert has_hamiltonian_path(g(["A", "B", "C"], [{"source": "A", "target": "B"}])) is False

    def test_complete_graph(self):
        assert has_hamiltonian_path(g(["A", "B", "C", "D"], [
            {"source": "A", "target": "B"}, {"source": "A", "target": "C"}, {"source": "A", "target": "D"},
            {"source": "B", "target": "C"}, {"source": "B", "target": "D"}, {"source": "C", "target": "D"},
        ])) is True

    def test_directed_path(self):
        assert has_hamiltonian_path(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}
        ], directed=True)) is True

    def test_directed_no_path(self):
        assert has_hamiltonian_path(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "C", "target": "B"}
        ], directed=True)) is False

    def test_empty_graph(self):
        assert has_hamiltonian_path(Graph(nodes=[], edges=[])) is False


class TestHamiltonianCycle:
    def test_triangle(self):
        assert has_hamiltonian_cycle(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ])) is True

    def test_path_no_cycle(self):
        assert has_hamiltonian_cycle(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}
        ])) is False

    def test_square(self):
        assert has_hamiltonian_cycle(g(["A", "B", "C", "D"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"},
            {"source": "C", "target": "D"}, {"source": "D", "target": "A"},
        ])) is True

    def test_petersen_has_no_hamiltonian_cycle(self):
        # The Petersen graph has no Hamiltonian cycle
        nodes = [f"o{i}" for i in range(5)] + [f"i{i}" for i in range(5)]
        edges = (
            [{"source": f"o{i}", "target": f"o{(i+1)%5}"} for i in range(5)] +
            [{"source": f"i{i}", "target": f"i{(i+2)%5}"} for i in range(5)] +
            [{"source": f"o{i}", "target": f"i{i}"} for i in range(5)]
        )
        assert has_hamiltonian_cycle(g(nodes, edges)) is False

    def test_two_nodes_no_cycle(self):
        assert has_hamiltonian_cycle(g(["A", "B"], [{"source": "A", "target": "B"}])) is False

    def test_directed_cycle(self):
        assert has_hamiltonian_cycle(g(["A", "B", "C"], [
            {"source": "A", "target": "B"}, {"source": "B", "target": "C"}, {"source": "C", "target": "A"}
        ], directed=True)) is True
