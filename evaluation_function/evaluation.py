from typing import Any, Callable, Optional, List, Dict, Tuple
from lf_toolkit.evaluation import Result, Params
from pydantic import ValidationError

from evaluation_function.algorithms import (
    bipartite_info,
    clique_number,
    connectivity_info,
    cycle_info,
    degree_sequence,
    has_hamiltonian_cycle,
    has_hamiltonian_path,
    is_complete,
    is_dag,
    is_eulerian,
    is_forest,
    is_n_colorable,
    is_planar,
    is_regular,
    is_semi_eulerian,
    is_subgraph,
    is_tree,
    isomorphism_info,
)
from evaluation_function.schemas import Answer, EvaluationParams, Graph, Response


from .schemas.graph import Graph, Node, Edge
from .schemas.request import Response, Answer
from .schemas.params import EvaluationParams
from .schemas.evaluation_types import EvaluationType


# =============================================================================
# FRONTEND FORMAT PARSER
# =============================================================================

def parse_frontend_graph(data: dict) -> Graph:
    """
    Parse pipe-delimited frontend graph format into a Graph object (nodes + edges only).

    Frontend format:
    - nodes: ["id|label|x|y", ...]
    - edges: ["source|target|weight|label", ...]

    Note: directed/weighted/multigraph are NOT read from the data dict here.
    They come exclusively from EvaluationParams and are applied later via
    _apply_params_to_graph().

    Args:
        data: Dictionary with pipe-delimited node and edge strings

    Returns:
        Graph object with only nodes and edges populated.
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
    
    # directed/weighted/multigraph are intentionally NOT read from the data dict.
    # They come exclusively from EvaluationParams, applied via _apply_params_to_graph().
    return Graph(nodes=nodes, edges=edges)


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
# GRAPH HELPERS
# =============================================================================

def _apply_params_to_graph(graph: Graph, params: EvaluationParams) -> Graph:
    """
    Return a new Graph with directed/weighted/multigraph copied from EvaluationParams.
    This is the single place where these flags are stamped onto a graph object —
    they must never come from the student or teacher payload.
    """
    return Graph(
        nodes=graph.nodes,
        edges=graph.edges,
        directed=params.directed,
        weighted=params.weighted,
        multigraph=params.multigraph,
    )


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

    # ── helpers ──────────────────────────────────────────────────────────

    def _to_dictish(obj: Any) -> Any:
        if obj is None:
            return None
        if isinstance(obj, (dict, list, str, int, float, bool)):
            return obj
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        if hasattr(obj, "dict"):
            return obj.dict()
        return obj

    def _ok() -> Result:
        return Result(is_correct=True)

    def _err(msg: str) -> Result:
        return Result(is_correct=False, feedback_items=[("error", msg + f"get answer: {answer}, response: {response}, params: {params}")])
    
    # return _err(f"answer: {answer}, response: {response}, params: {params}")

    # ── parse answer FIRST — evaluation_type and graph flags now live here ─────

    answer_dict = _to_dictish(answer) or {}

    if is_frontend_format(answer_dict):
        parsed_graph = parse_frontend_graph(answer_dict)
        answer_dict = {"graph": parsed_graph.model_dump()}

    try:
        ans = Answer.model_validate(answer_dict)
    except ValidationError as e:
        return _err(f"Invalid answer schema: {e}")

    # ── extract evaluation params from answer ─────────────────────────────
    # All evaluation configuration now comes from the answer object
    
    eval_params_dict = {}
    
    # Get evaluation_type from answer (required)
    if ans.evaluation_type:
        eval_params_dict['evaluation_type'] = ans.evaluation_type
    elif 'evaluation_type' in answer_dict:
        eval_params_dict['evaluation_type'] = answer_dict['evaluation_type']
    else:
        # return _err("evaluation_type is required in answer object")
        eval_params_dict['evaluation_type'] = "isomorphism"  # default to isomorphism for backward compatibility with old tests that don't specify it
    
    # Get graph structure flags from answer (with defaults)
    eval_params_dict['directed'] = ans.directed if ans.directed is not None else False
    eval_params_dict['weighted'] = ans.weighted if ans.weighted is not None else False
    eval_params_dict['multigraph'] = ans.multigraph if ans.multigraph is not None else False
    
    # Get optional evaluation sub-params from answer
    for key in ['connectivity', 'bipartite', 'graph_coloring', 'cycle_detection', 
                'isomorphism', 'feedback_level', 'tolerance']:
        value = getattr(ans, key, None)
        if value is not None:
            eval_params_dict[key] = value
    
    # Set defaults for feedback_level and tolerance if not provided
    if 'feedback_level' not in eval_params_dict:
        eval_params_dict['feedback_level'] = 'standard'
    if 'tolerance' not in eval_params_dict:
        eval_params_dict['tolerance'] = 1e-9
    
    try:
        p = EvaluationParams.model_validate(eval_params_dict)
    except ValidationError as e:
        return _err(f"Invalid evaluation parameters in answer: {e}")

    # ── parse response (student's graph) ─────────────────────────────────

    response_dict = _to_dictish(response) or {}

    if is_frontend_format(response_dict):
        parsed_graph = parse_frontend_graph(response_dict)
        response_dict = {"graph": parsed_graph.model_dump()}

    try:
        resp = Response.model_validate(response_dict)
    except ValidationError as e:
        return _err(f"Invalid response schema: {e}")

    # ── resolve graphs and stamp params flags ─────────────────────────────
    # directed/weighted/multigraph come exclusively from answer object — never from
    # the student response payload.

    student_graph: Graph = resp.graph
    if student_graph is None:
        return _err("response.graph is required — the student must submit a graph.")

    student_graph = _apply_params_to_graph(student_graph, p)

    if ans.graph is not None:
        ans = ans.model_copy(update={"graph": _apply_params_to_graph(ans.graph, p)})

    # ── helper: grade a simple boolean property ──────────────────────────
    def _grade_bool(
        label: str,
        compute_fn: Callable[[Graph], bool],
    ) -> Result:
        """Check if the student's graph has the specified property."""
        has_property = compute_fn(student_graph)
        if has_property:
            return _ok()
        return _err(f"{label}: The graph does not have this property.")

    # ── evaluation-type handlers ─────────────────────────────────────────

    def _eval_connectivity() -> Result:
        """Check if the student's graph is connected."""
        conn_params = p.connectivity
        check_type = conn_params.check_type if conn_params else "connected"

        result = connectivity_info(
            student_graph, connectivity_type=check_type, return_components=True
        )

        if result.is_connected:
            return _ok()

        fb = f"Connectivity ({check_type}): Graph is not connected."
        if result.components is not None:
            fb += f" Found {len(result.components)} components: {result.components}."
        return _err(fb)

    def _eval_bipartite() -> Result:
        """Check if the student's graph is bipartite."""
        b_params = p.bipartite
        want_parts = bool(b_params.return_partitions) if b_params else False
        want_odd = bool(b_params.return_odd_cycle) if b_params else True

        result = bipartite_info(student_graph, return_partitions=want_parts, return_odd_cycle=want_odd)

        if result.is_bipartite:
            return _ok()

        fb = "Bipartite: Graph is not bipartite."
        if want_odd and result.odd_cycle is not None:
            fb += f" Found odd cycle: {result.odd_cycle}."
        return _err(fb)

    def _eval_cycle_detection() -> Result:
        """Check if the student's graph has a cycle."""
        result = cycle_info(student_graph)

        if result.has_cycle:
            return _ok()

        return _err("Cycle detection: Graph does not contain a cycle.")

    def _eval_graph_coloring() -> Result:
        """Check if the student's graph is k-colorable."""
        gc_params = p.graph_coloring
        num_colors = gc_params.num_colors if (gc_params and gc_params.num_colors is not None) else ans.num_colors
        if num_colors is None:
            return _err("Missing num_colors: provide in answer.num_colors.")

        student_coloring = resp.coloring

        # If student provided a coloring, validate it
        if student_coloring is not None:
            adj: dict[str, set[str]] = {n.id: set() for n in student_graph.nodes}
            for e in student_graph.edges:
                adj[e.source].add(e.target)
                if not student_graph.directed:
                    adj[e.target].add(e.source)

            valid_coloring = True
            invalid_reason = ""
            node_ids = {n.id for n in student_graph.nodes}
            for nid in node_ids:
                if nid not in student_coloring:
                    valid_coloring = False
                    invalid_reason = f"Node '{nid}' has no color assigned."
                    break
            if valid_coloring:
                for nid, color in student_coloring.items():
                    if color < 0 or color >= num_colors:
                        valid_coloring = False
                        invalid_reason = f"Node '{nid}' has color {color}, but only {num_colors} colors (0..{num_colors - 1}) are allowed."
                        break
                    for nb in adj.get(nid, set()):
                        if student_coloring.get(nb) == color:
                            valid_coloring = False
                            invalid_reason = f"Adjacent nodes '{nid}' and '{nb}' share color {color}."
                            break
                    if not valid_coloring:
                        break

            if not valid_coloring:
                return _err(f"Graph coloring ({num_colors}-coloring): invalid coloring. {invalid_reason}")
            return _ok()

        # Otherwise, check if the graph is k-colorable
        result = is_n_colorable(student_graph, num_colors)

        if result.is_colorable:
            return _ok()

        return _err(f"Graph coloring: Graph is not {num_colors}-colorable.")

    def _eval_isomorphism() -> Result:
        """Check if the student's graph is isomorphic to the reference graph."""
        if ans.graph is None:
            return _err("Isomorphism requires answer.graph (the reference graph).")

        result = isomorphism_info(ans.graph, student_graph)

        if result.is_isomorphic:
            return _ok()

        return _err("Isomorphism: Graphs are not isomorphic.")

    def _eval_planarity() -> Result:
        return _grade_bool("Planarity", is_planar)

    def _eval_tree() -> Result:
        return _grade_bool("Tree", is_tree)

    def _eval_forest() -> Result:
        return _grade_bool("Forest", is_forest)

    def _eval_dag() -> Result:
        if not student_graph.directed:
            return _err("DAG check requires a directed graph.")
        return _grade_bool("DAG", is_dag)

    def _eval_eulerian() -> Result:
        return _grade_bool("Eulerian circuit", is_eulerian)

    def _eval_semi_eulerian() -> Result:
        return _grade_bool("Semi-Eulerian (Euler path)", is_semi_eulerian)

    def _eval_regular() -> Result:
        return _grade_bool("Regular", is_regular)

    def _eval_complete() -> Result:
        return _grade_bool("Complete", is_complete)

    def _eval_degree_sequence() -> Result:
        """Compute and return the degree sequence of the student's graph."""
        # For degree_sequence, we just compute it and return success
        # The actual sequence can be retrieved from the graph
        student_seq = degree_sequence(student_graph)
        return _ok()

    def _eval_subgraph() -> Result:
        if ans.graph is None:
            return _err("Subgraph check requires answer.graph (the parent graph from the teacher).")

        result = is_subgraph(student_graph, ans.graph)
        if result:
            return _ok()
        return _err("Subgraph: the student's graph is NOT a subgraph of the teacher's graph.")

    def _eval_hamiltonian_path() -> Result:
        return _grade_bool("Hamiltonian path", has_hamiltonian_path)

    def _eval_hamiltonian_cycle() -> Result:
        return _grade_bool("Hamiltonian cycle", has_hamiltonian_cycle)

    def _eval_clique_number() -> Result:
        """Compute the clique number of the student's graph."""
        # For clique_number, we just compute it and return success
        student_cn = clique_number(student_graph)
        return _ok()

    # ── dispatch ─────────────────────────────────────────────────────────

    dispatch: dict[str, Callable[[], Result]] = {
        "connectivity": _eval_connectivity,
        "bipartite": _eval_bipartite,
        "cycle_detection": _eval_cycle_detection,
        "graph_coloring": _eval_graph_coloring,
        "isomorphism": _eval_isomorphism,
        "planarity": _eval_planarity,
        "tree": _eval_tree,
        "forest": _eval_forest,
        "dag": _eval_dag,
        "eulerian": _eval_eulerian,
        "semi_eulerian": _eval_semi_eulerian,
        "regular": _eval_regular,
        "complete": _eval_complete,
        "degree_sequence": _eval_degree_sequence,
        "subgraph": _eval_subgraph,
        "hamiltonian_path": _eval_hamiltonian_path,
        "hamiltonian_cycle": _eval_hamiltonian_cycle,
        "clique_number": _eval_clique_number,
    }

    # Always use the evaluation type from params
    handler = dispatch.get(p.evaluation_type)
    if handler is None:
        return _err(f"Unsupported evaluation_type: '{p.evaluation_type}'.")
    return handler()
