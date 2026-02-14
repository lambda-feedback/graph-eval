from lf_toolkit.evaluation import Params

from evaluation_function.evaluation import evaluation_function


def test_evaluation_connectivity_property_question():
    # Question graph is in answer.graph; student provides boolean.
    answer = {
        "graph": {"nodes": [{"id": "A"}, {"id": "B"}], "edges": [{"source": "A", "target": "B"}], "directed": False},
        "is_connected": True,
    }
    response = {"is_connected": True}
    params = {"evaluation_type": "connectivity", "connectivity": {"check_type": "connected"}}
    result = evaluation_function(response, answer, Params(params)).to_dict()
    assert result["is_correct"] is True


def test_evaluation_bipartite_graph_building_task():
    # Student builds a bipartite graph; answer encodes the property.
    answer = {"is_bipartite": True}
    response = {
        "graph": {
            "nodes": [{"id": "A"}, {"id": "B"}, {"id": "X"}],
            "edges": [{"source": "A", "target": "X"}, {"source": "B", "target": "X"}],
            "directed": False,
        }
    }
    params = {"evaluation_type": "bipartite"}
    result = evaluation_function(response, answer, Params(params)).to_dict()
    assert result["is_correct"] is True


def test_evaluation_shortest_path_distance():
    answer = {
        "graph": {
            "nodes": [{"id": "A"}, {"id": "B"}, {"id": "C"}],
            "edges": [{"source": "A", "target": "B"}, {"source": "B", "target": "C"}],
            "directed": False,
        },
        "shortest_distance": 2,
    }
    response = {"distance": 2}
    params = {"evaluation_type": "shortest_path", "shortest_path": {"source_node": "A", "target_node": "C", "algorithm": "auto"}}
    result = evaluation_function(response, answer, Params(params)).to_dict()
    assert result["is_correct"] is True

