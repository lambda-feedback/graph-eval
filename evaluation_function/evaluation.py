from typing import Any, Optional, List, Dict, Tuple
from lf_toolkit.evaluation import Result, Params

from .schemas.graph import Graph, Node, Edge
from .schemas.request import Response, Answer
from .schemas.params import EvaluationParams
from .schemas.evaluation_types import EvaluationType


# =============================================================================
# FRONTEND FORMAT PARSER
# =============================================================================

def parse_frontend_graph(data: dict) -> Graph:
    """
    Parse pipe-delimited frontend graph format into Graph object.
    
    Frontend format:
    - nodes: ["id|label|x|y", ...]
    - edges: ["source|target|weight|label", ...]
    - directed: boolean
    - weighted: boolean
    - multigraph: boolean
    
    Example:
        {
          "nodes": ["city1|New York|120|180"],
          "edges": ["city1|city2|215|I-95 North"],
          "directed": true,
          "weighted": true,
          "multigraph": false
        }
    
    Args:
        data: Dictionary with pipe-delimited node and edge strings
        
    Returns:
        Graph object with parsed nodes and edges
    """
    nodes = []
    edges = []
    
    # Parse nodes: "id|label|x|y"
    for node_str in data.get("nodes", []):
        if not isinstance(node_str, str):
            continue
            
        parts = node_str.split("|")
        if len(parts) >= 1:
            node = Node(
                id=parts[0],
                label=parts[1] if len(parts) > 1 else parts[0],
                x=float(parts[2]) if len(parts) > 2 and parts[2] else None,
                y=float(parts[3]) if len(parts) > 3 and parts[3] else None
            )
            nodes.append(node)
    
    # Parse edges: "source|target|weight|label"
    for edge_str in data.get("edges", []):
        if not isinstance(edge_str, str):
            continue
            
        parts = edge_str.split("|")
        if len(parts) >= 2:
            edge = Edge(
                source=parts[0],
                target=parts[1],
                weight=float(parts[2]) if len(parts) > 2 and parts[2] and parts[2].replace('.', '').replace('-', '').isdigit() else None,
                label=parts[3] if len(parts) > 3 else None
            )
            edges.append(edge)
    
    return Graph(
        nodes=nodes,
        edges=edges,
        directed=data.get("directed", False),
        weighted=data.get("weighted", False),
        multigraph=data.get("multigraph", False)
    )


def is_frontend_format(data: dict) -> bool:
    """
    Check if the data is in frontend pipe-delimited format.
    
    Args:
        data: Dictionary to check
        
    Returns:
        True if data appears to be in frontend format
    """
    if not isinstance(data, dict):
        return False
    
    # Check if it has nodes field with string elements
    nodes = data.get("nodes", [])
    if nodes and isinstance(nodes, list) and len(nodes) > 0:
        # Check if first node is a pipe-delimited string
        first_node = nodes[0]
        if isinstance(first_node, str) and "|" in first_node:
            return True
    
    # Also check edges
    edges = data.get("edges", [])
    if edges and isinstance(edges, list) and len(edges) > 0:
        first_edge = edges[0]
        if isinstance(first_edge, str) and "|" in first_edge:
            return True
    
    return False


# =============================================================================
# FEEDBACK GENERATION HELPERS
# =============================================================================

def create_feedback_message(
    is_correct: bool,
    feedback_level: str,
    error_details: List[str] = None,
    success_details: List[str] = None,
    hints: List[str] = None
) -> str:
    """Generate a feedback message based on feedback level."""
    
    if feedback_level == "minimal":
        return "Correct" if is_correct else "Incorrect"
    
    feedback_parts = []
    
    if is_correct:
        feedback_parts.append("✓ Correct")
        if feedback_level == "detailed" and success_details:
            feedback_parts.extend(success_details)
    else:
        feedback_parts.append("✗ Incorrect")
        if error_details:
            feedback_parts.extend(error_details)
        if feedback_level == "detailed" and hints:
            feedback_parts.append("\nHints:")
            feedback_parts.extend([f"  • {hint}" for hint in hints])
    
    return "\n".join(feedback_parts)


def compare_graphs(response_graph: Graph, answer_graph: Graph, tolerance: float = 1e-9) -> Tuple[bool, List[str]]:
    """
    Compare two graphs and return (is_match, error_details).
    """
    errors = []
    
    # Check nodes
    response_node_ids = {node.id for node in response_graph.nodes}
    answer_node_ids = {node.id for node in answer_graph.nodes}
    
    missing_nodes = answer_node_ids - response_node_ids
    extra_nodes = response_node_ids - answer_node_ids
    
    if missing_nodes:
        errors.append(f"Missing nodes: {', '.join(sorted(missing_nodes))}")
    if extra_nodes:
        errors.append(f"Extra nodes: {', '.join(sorted(extra_nodes))}")
    
    # Check edges (if nodes match)
    if not missing_nodes and not extra_nodes:
        response_edges = {(e.source, e.target) for e in response_graph.edges}
        answer_edges = {(e.source, e.target) for e in answer_graph.edges}
        
        # For undirected graphs, normalize edge representation
        if not response_graph.directed:
            response_edges = {tuple(sorted([s, t])) for s, t in response_edges}
            answer_edges = {tuple(sorted([s, t])) for s, t in answer_edges}
        
        missing_edges = answer_edges - response_edges
        extra_edges = response_edges - answer_edges
        
        if missing_edges:
            arrow = "→" if response_graph.directed else "—"
            edges_str = ", ".join([f"{s}{arrow}{t}" for s, t in sorted(missing_edges)])
            errors.append(f"Missing edges: {edges_str}")
        if extra_edges:
            arrow = "→" if response_graph.directed else "—"
            edges_str = ", ".join([f"{s}{arrow}{t}" for s, t in sorted(extra_edges)])
            errors.append(f"Extra edges: {edges_str}")
        
        # Check edge weights if weighted
        if response_graph.weighted and not missing_edges and not extra_edges:
            for r_edge in response_graph.edges:
                a_edge = next((e for e in answer_graph.edges 
                             if e.source == r_edge.source and e.target == r_edge.target), None)
                if a_edge and abs((r_edge.weight or 0) - (a_edge.weight or 0)) > tolerance:
                    errors.append(
                        f"Edge {r_edge.source}→{r_edge.target} has incorrect weight "
                        f"(your answer: {r_edge.weight}, expected: {a_edge.weight})"
                    )
    
    return len(errors) == 0, errors


def validate_path(path: List[str], graph: Graph) -> Tuple[bool, List[str]]:
    """
    Validate that a path exists in the graph.
    Returns (is_valid, error_details).
    """
    if not path:
        return False, ["Path is empty"]
    
    errors = []
    node_ids = {node.id for node in graph.nodes}
    
    # Check all nodes exist
    for node_id in path:
        if node_id not in node_ids:
            errors.append(f"Node '{node_id}' does not exist in the graph")
    
    if errors:
        return False, errors
    
    # Check edges exist
    edge_set = {(e.source, e.target) for e in graph.edges}
    if not graph.directed:
        # For undirected, edges work both ways
        edge_set = edge_set.union({(t, s) for s, t in edge_set})
    
    for i in range(len(path) - 1):
        edge = (path[i], path[i + 1])
        if edge not in edge_set:
            arrow = "→" if graph.directed else "—"
            errors.append(f"Edge {edge[0]}{arrow}{edge[1]} does not exist in the graph")
    
    return len(errors) == 0, errors


def validate_coloring(coloring: Dict[str, int], graph: Graph) -> Tuple[bool, List[str], List[Tuple[str, str]]]:
    """
    Validate a graph coloring.
    Returns (is_valid, error_details, conflicts).
    """
    errors = []
    conflicts = []
    
    node_ids = {node.id for node in graph.nodes}
    
    # Check all nodes are colored
    missing_nodes = node_ids - set(coloring.keys())
    if missing_nodes:
        errors.append(f"Nodes not colored: {', '.join(sorted(missing_nodes))}")
    
    extra_nodes = set(coloring.keys()) - node_ids
    if extra_nodes:
        errors.append(f"Colored non-existent nodes: {', '.join(sorted(extra_nodes))}")
    
    if errors:
        return False, errors, conflicts
    
    # Check for conflicts (adjacent nodes with same color)
    for edge in graph.edges:
        source_color = coloring.get(edge.source)
        target_color = coloring.get(edge.target)
        
        if source_color is not None and source_color == target_color:
            conflicts.append((edge.source, edge.target))
            errors.append(
                f"Color conflict: adjacent nodes {edge.source} and {edge.target} "
                f"both have color {source_color}"
            )
    
    return len(errors) == 0, errors, conflicts


def validate_vertex_set(vertices: List[str], graph: Graph, set_type: str = "set") -> Tuple[bool, List[str]]:
    """
    Validate that vertices exist in the graph.
    Returns (is_valid, error_details).
    """
    if not vertices:
        return True, []
    
    errors = []
    node_ids = {node.id for node in graph.nodes}
    
    invalid_nodes = set(vertices) - node_ids
    if invalid_nodes:
        errors.append(f"{set_type} contains non-existent nodes: {', '.join(sorted(invalid_nodes))}")
    
    return len(errors) == 0, errors


def check_tree_edges(edges: List[Edge], graph: Graph) -> Tuple[bool, List[str]]:
    """
    Check if given edges form a valid tree (connected, acyclic, n-1 edges).
    Returns (is_tree, error_details).
    """
    errors = []
    n = len(graph.nodes)
    
    # Check edge count but continue checking for other issues
    if len(edges) != n - 1:
        errors.append(f"Tree must have {n-1} edges (you provided {len(edges)})")
    
    # Check all edges exist in graph
    graph_edges = {(e.source, e.target) for e in graph.edges}
    if not graph.directed:
        graph_edges = graph_edges.union({(t, s) for s, t in graph_edges})
    
    for edge in edges:
        if (edge.source, edge.target) not in graph_edges:
            errors.append(f"Edge {edge.source}—{edge.target} does not exist in the original graph")
    
    # Check connectivity using union-find
    parent = {node.id: node.id for node in graph.nodes}
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        px, py = find(x), find(y)
        if px == py:
            return False  # Cycle detected
        parent[px] = py
        return True
    
    for edge in edges:
        if not union(edge.source, edge.target):
            errors.append(f"Edges form a cycle (edge {edge.source}—{edge.target} creates cycle)")
    
    # Check if all nodes are connected
    roots = {find(node.id) for node in graph.nodes}
    if len(roots) > 1:
        errors.append(f"Edges do not form a connected tree ({len(roots)} components)")
    
    # Return True only if no errors
    return len(errors) == 0, errors


# =============================================================================
# EVALUATION FUNCTIONS BY TYPE
# =============================================================================

def evaluate_graph_match(response: Response, answer: Answer, params: EvaluationParams) -> Tuple[bool, str]:
    """Evaluate graph matching."""
    if not response.graph or not answer.graph:
        return False, "Missing graph in response or answer"
    
    is_match, errors = compare_graphs(response.graph, answer.graph, params.tolerance)
    
    if is_match:
        return True, create_feedback_message(True, params.feedback_level, 
                                             success_details=["Graph structure matches correctly"])
    else:
        hints = ["Check your nodes and edges carefully", 
                "Make sure edge directions match (if directed graph)"]
        return False, create_feedback_message(False, params.feedback_level, 
                                              error_details=errors, hints=hints)


def evaluate_path_answer(response: Response, answer: Answer, params: EvaluationParams, 
                         path_field: str = "path") -> Tuple[bool, str]:
    """Evaluate a path answer."""
    response_path = getattr(response, path_field, None)
    answer_path = getattr(answer, path_field, None)
    
    if not response_path:
        return False, create_feedback_message(False, params.feedback_level,
                                              error_details=["No path provided"])
    
    if not answer.graph:
        # Simple comparison if no graph provided
        is_correct = response_path == answer_path
        if is_correct:
            return True, create_feedback_message(True, params.feedback_level)
        else:
            return False, create_feedback_message(False, params.feedback_level,
                                                  error_details=["Path does not match expected answer"])
    
    # Validate path exists in graph
    is_valid, errors = validate_path(response_path, answer.graph)
    if not is_valid:
        return False, create_feedback_message(False, params.feedback_level,
                                              error_details=errors,
                                              hints=["Verify all edges exist in the graph"])
    
    # Check if path matches expected
    is_correct = response_path == answer_path
    if is_correct:
        return True, create_feedback_message(True, params.feedback_level,
                                             success_details=["Path is correct"])
    else:
        path_str = " → ".join(response_path)
        expected_str = " → ".join(answer_path) if answer_path else "different path"
        return False, create_feedback_message(False, params.feedback_level,
                                              error_details=[f"Your path: {path_str}",
                                                           f"Expected: {expected_str}"])


def evaluate_boolean_answer(response: Response, answer: Answer, params: EvaluationParams,
                           field_name: str, display_name: str) -> Tuple[bool, str]:
    """Evaluate a boolean answer."""
    response_value = getattr(response, field_name, None)
    answer_value = getattr(answer, field_name, None)
    
    if response_value is None:
        return False, create_feedback_message(False, params.feedback_level,
                                              error_details=[f"No answer provided for {display_name}"])
    
    is_correct = response_value == answer_value
    
    if is_correct:
        return True, create_feedback_message(True, params.feedback_level,
                                             success_details=[f"{display_name}: {'Yes' if response_value else 'No'} ✓"])
    else:
        expected = "Yes" if answer_value else "No"
        got = "Yes" if response_value else "No"
        return False, create_feedback_message(False, params.feedback_level,
                                              error_details=[f"{display_name}: You answered {got}, but the correct answer is {expected}"])


def evaluate_numeric_answer(response: Response, answer: Answer, params: EvaluationParams,
                           field_name: str, display_name: str) -> Tuple[bool, str]:
    """Evaluate a numeric answer."""
    response_value = getattr(response, field_name, None)
    answer_value = getattr(answer, field_name, None)
    
    if response_value is None:
        return False, create_feedback_message(False, params.feedback_level,
                                              error_details=[f"No answer provided for {display_name}"])
    
    if answer_value is None:
        return False, "No expected answer provided"
    
    is_correct = abs(response_value - answer_value) <= params.tolerance
    
    if is_correct:
        return True, create_feedback_message(True, params.feedback_level,
                                             success_details=[f"{display_name}: {response_value} ✓"])
    else:
        return False, create_feedback_message(False, params.feedback_level,
                                              error_details=[f"{display_name}: You got {response_value}, expected {answer_value}"],
                                              hints=[f"The difference is {abs(response_value - answer_value):.4f}"])


def evaluate_coloring_answer(response: Response, answer: Answer, params: EvaluationParams) -> Tuple[bool, str]:
    """Evaluate a graph coloring answer."""
    if not response.coloring:
        return False, create_feedback_message(False, params.feedback_level,
                                              error_details=["No coloring provided"])
    
    if not answer.graph:
        return False, "No graph provided for validation"
    
    is_valid, errors, conflicts = validate_coloring(response.coloring, answer.graph)
    
    if not is_valid:
        hints = ["Adjacent nodes must have different colors",
                "Make sure all nodes are colored"]
        return False, create_feedback_message(False, params.feedback_level,
                                              error_details=errors, hints=hints)
    
    # Check chromatic number if provided
    if answer.chromatic_number is not None and response.chromatic_number is not None:
        num_colors = len(set(response.coloring.values()))
        if num_colors > answer.chromatic_number:
            return False, create_feedback_message(False, params.feedback_level,
                                                  error_details=[f"Your coloring uses {num_colors} colors, "
                                                               f"but the graph can be colored with {answer.chromatic_number} colors"],
                                                  hints=["Try to reduce the number of colors used"])
    
    return True, create_feedback_message(True, params.feedback_level,
                                         success_details=["Valid coloring ✓"])


def evaluate_set_answer(response: Response, answer: Answer, params: EvaluationParams,
                       field_name: str, display_name: str) -> Tuple[bool, str]:
    """Evaluate a set-based answer (vertex cover, independent set, etc.)."""
    response_set = getattr(response, field_name, None)
    answer_set = getattr(answer, field_name, None)
    
    if not response_set:
        return False, create_feedback_message(False, params.feedback_level,
                                              error_details=[f"No {display_name} provided"])
    
    if answer.graph:
        is_valid, errors = validate_vertex_set(response_set, answer.graph, display_name)
        if not is_valid:
            return False, create_feedback_message(False, params.feedback_level,
                                                  error_details=errors)
    
    # Compare sets (order doesn't matter)
    if answer_set:
        is_correct = set(response_set) == set(answer_set)
        if is_correct:
            return True, create_feedback_message(True, params.feedback_level,
                                                 success_details=[f"{display_name} is correct ✓"])
        else:
            missing = set(answer_set) - set(response_set)
            extra = set(response_set) - set(answer_set)
            errors = []
            if missing:
                errors.append(f"Missing from {display_name}: {', '.join(sorted(missing))}")
            if extra:
                errors.append(f"Extra in {display_name}: {', '.join(sorted(extra))}")
            return False, create_feedback_message(False, params.feedback_level,
                                                  error_details=errors)
    
    return True, create_feedback_message(True, params.feedback_level)


def evaluate_tree_answer(response: Response, answer: Answer, params: EvaluationParams,
                        field_name: str = "spanning_tree") -> Tuple[bool, str]:
    """Evaluate a spanning tree answer."""
    response_edges = getattr(response, field_name, None)
    
    if not response_edges:
        return False, create_feedback_message(False, params.feedback_level,
                                              error_details=["No tree edges provided"])
    
    if not answer.graph:
        return False, "No graph provided for validation"
    
    is_tree, errors = check_tree_edges(response_edges, answer.graph)
    
    if not is_tree:
        hints = ["A tree must be connected and acyclic",
                f"A tree with {len(answer.graph.nodes)} nodes must have exactly {len(answer.graph.nodes)-1} edges"]
        return False, create_feedback_message(False, params.feedback_level,
                                              error_details=errors, hints=hints)
    
    # Check MST weight if applicable
    if field_name == "mst" and answer.mst_weight is not None:
        total_weight = sum(edge.weight or 0 for edge in response_edges)
        if abs(total_weight - answer.mst_weight) > params.tolerance:
            return False, create_feedback_message(False, params.feedback_level,
                                                  error_details=[f"Your tree has weight {total_weight}, "
                                                               f"but minimum spanning tree has weight {answer.mst_weight}"],
                                                  hints=["Try using Kruskal's or Prim's algorithm"])
    
    return True, create_feedback_message(True, params.feedback_level,
                                         success_details=["Valid spanning tree ✓"])


# =============================================================================
# MAIN EVALUATION FUNCTION
# =============================================================================

def evaluation_function(
    response: Any,
    answer: Any,
    params: Params,
) -> Result:
    """
    Function used to evaluate a student response.
    ---
    The handler function passes three arguments to evaluation_function():

    - `response` which are the answers provided by the student.
    - `answer` which are the correct answers to compare against.
    - `params` which are any extra parameters that may be useful,
        e.g., error tolerances.

    The output of this function is what is returned as the API response
    and therefore must be JSON-encodable. It must also conform to the
    response schema.

    Any standard python library may be used, as well as any package
    available on pip (provided it is added to requirements.txt).

    The way you wish to structure you code (all in this function, or
    split into many) is entirely up to you. All that matters are the
    return types and that evaluation_function() is the main function used
    to output the evaluation response.
    """
    
    try:
        # Parse inputs - handle both frontend pipe-delimited and standard formats
        if isinstance(response, dict):
            # Check if it's frontend pipe-delimited format
            if is_frontend_format(response):
                parsed_graph = parse_frontend_graph(response)
                response_obj = Response(graph=parsed_graph)
            else:
                response_obj = Response(**response)
        elif isinstance(response, Response):
            response_obj = response
        else:
            return Result(is_correct=False, feedback_items=[('error', 'Invalid response format')])
        
        if isinstance(answer, dict):
            # Check if it's frontend pipe-delimited format
            if is_frontend_format(answer):
                parsed_graph = parse_frontend_graph(answer)
                answer_obj = Answer(graph=parsed_graph)
            else:
                answer_obj = Answer(**answer)
        elif isinstance(answer, Answer):
            answer_obj = answer
        else:
            return Result(is_correct=False, feedback_items=[('error', 'Invalid answer format')])
        
        if isinstance(params, dict):
            eval_params = EvaluationParams(**params)
        elif isinstance(params, EvaluationParams):
            eval_params = params
        else:
            # Use defaults
            eval_params = EvaluationParams(
                evaluation_type=EvaluationType.GRAPH_MATCH,
                feedback_level="standard",
                tolerance=1e-9
            )
        
        # Helper to convert tuple to Result
        def make_result(eval_result):
            is_correct, feedback = eval_result
            # Result expects feedback_items as a list of tuples
            # We pass feedback as a single tuple
            feedback_items = [('feedback', feedback)] if feedback else []
            return Result(is_correct=is_correct, feedback_items=feedback_items)
        
        # Route to appropriate evaluation based on evaluation type or available fields
        evaluation_type = getattr(eval_params, 'evaluation_type', None)
        
        # Graph matching
        if evaluation_type == "graph_match" or (response_obj.graph and answer_obj.graph and not evaluation_type):
            return make_result(evaluate_graph_match(response_obj, answer_obj, eval_params))
        
        # Boolean answers
        if response_obj.is_connected is not None or answer_obj.is_connected is not None:
            return make_result(evaluate_boolean_answer(response_obj, answer_obj, eval_params,
                                                   "is_connected", "Connectivity"))
        if response_obj.is_bipartite is not None or answer_obj.is_bipartite is not None:
            return make_result(evaluate_boolean_answer(response_obj, answer_obj, eval_params,
                                                   "is_bipartite", "Bipartite"))
        if response_obj.is_tree is not None or answer_obj.is_tree is not None:
            return make_result(evaluate_boolean_answer(response_obj, answer_obj, eval_params,
                                                   "is_tree", "Tree"))
        if response_obj.has_cycle is not None or answer_obj.has_cycle is not None:
            return make_result(evaluate_boolean_answer(response_obj, answer_obj, eval_params,
                                                   "has_cycle", "Cycle Detection"))
        
        # Path answers
        if response_obj.path is not None or answer_obj.path is not None:
            return make_result(evaluate_path_answer(response_obj, answer_obj, eval_params, "path"))
        if response_obj.topological_order is not None or answer_obj.topological_order is not None:
            return make_result(evaluate_path_answer(response_obj, answer_obj, eval_params, "topological_order"))
        
        # Numeric answers
        if response_obj.distance is not None or answer_obj.distance is not None:
            return make_result(evaluate_numeric_answer(response_obj, answer_obj, eval_params,
                                                   "distance", "Distance"))
        if response_obj.chromatic_number is not None or answer_obj.chromatic_number is not None:
            return make_result(evaluate_numeric_answer(response_obj, answer_obj, eval_params,
                                                   "chromatic_number", "Chromatic Number"))
        if response_obj.flow_value is not None or answer_obj.flow_value is not None:
            return make_result(evaluate_numeric_answer(response_obj, answer_obj, eval_params,
                                                   "flow_value", "Maximum Flow"))
        
        # Coloring
        if response_obj.coloring is not None:
            return make_result(evaluate_coloring_answer(response_obj, answer_obj, eval_params))
        
        # Set answers
        if response_obj.vertex_cover is not None or answer_obj.vertex_cover is not None:
            return make_result(evaluate_set_answer(response_obj, answer_obj, eval_params,
                                              "vertex_cover", "Vertex Cover"))
        if response_obj.independent_set is not None or answer_obj.independent_set is not None:
            return make_result(evaluate_set_answer(response_obj, answer_obj, eval_params,
                                              "independent_set", "Independent Set"))
        if response_obj.clique is not None or answer_obj.clique is not None:
            return make_result(evaluate_set_answer(response_obj, answer_obj, eval_params,
                                              "clique", "Clique"))
        
        # Tree answers
        if response_obj.spanning_tree is not None or answer_obj.spanning_tree is not None:
            return make_result(evaluate_tree_answer(response_obj, answer_obj, eval_params, "spanning_tree"))
        if response_obj.mst is not None or answer_obj.mst is not None:
            return make_result(evaluate_tree_answer(response_obj, answer_obj, eval_params, "mst"))
        
        # Default: simple equality check
        is_correct = response == answer
        feedback = "Correct" if is_correct else "Incorrect"
        return Result(is_correct=is_correct, feedback_items=[('feedback', feedback)])
        
    except Exception as e:
        return Result(is_correct=False, feedback_items=[('error', f'Evaluation error: {str(e)}')])