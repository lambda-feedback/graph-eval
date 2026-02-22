"""
Preview function for Graph validation.

The preview function validates student graph responses BEFORE submission.
It catches clear structural errors early, preventing students from submitting
invalid graphs for full evaluation.

Validation checks performed:
1. Parse check - Is the response a valid graph structure?
2. Structural validation - Are nodes and edges valid?
3. Consistency checks - Edge references, weights, capacities, etc.
4. Warnings - Isolated nodes, disconnected components, etc.
"""

from typing import Any, List, Dict, Set, Optional
from lf_toolkit.preview import Result, Params, Preview

from .schemas.graph import Graph, Node, Edge
from .schemas.request import Response


# =============================================================================
# VALIDATION ERROR CLASSES
# =============================================================================

class ValidationError:
    """Represents a validation error or warning."""
    
    def __init__(
        self,
        message: str,
        code: str,
        severity: str = "error",
        location: Optional[str] = None,
        suggestion: Optional[str] = None
    ):
        self.message = message
        self.code = code
        self.severity = severity  # "error" or "warning"
        self.location = location
        self.suggestion = suggestion


# =============================================================================
# GRAPH PARSING
# =============================================================================

def parse_graph_response(value: Any) -> Response:
    """
    Parse a graph response from various input formats.
    
    Args:
        value: Response as dict or JSON string
        
    Returns:
        Parsed Response object
        
    Raises:
        ValueError: If the input cannot be parsed as a valid response
    """
    if value is None:
        raise ValueError("No response provided")
    
    if isinstance(value, str):
        # Try to parse as JSON string
        return Response.model_validate_json(value)
    elif isinstance(value, dict):
        return Response.model_validate(value)
    elif isinstance(value, Response):
        return value
    else:
        raise ValueError(f"Expected response as dict or JSON string, got {type(value).__name__}")


# =============================================================================
# GRAPH VALIDATION
# =============================================================================

def validate_graph_structure(graph: Graph) -> List[ValidationError]:
    """
    Validate the structural integrity of a graph.
    
    Checks:
    - Node IDs are unique
    - Edges reference existing nodes
    - No duplicate edges (unless multigraph)
    - Edge weights are valid numbers
    - Capacities/flows are valid (for flow networks)
    """
    errors = []
    
    # Check node uniqueness
    node_ids = [node.id for node in graph.nodes]
    node_id_set = set(node_ids)
    
    if len(node_ids) != len(node_id_set):
        duplicates = [nid for nid in node_id_set if node_ids.count(nid) > 1]
        errors.append(ValidationError(
            message=f"Duplicate node IDs found: {', '.join(duplicates)}",
            code="DUPLICATE_NODES",
            severity="error",
            suggestion="Each node must have a unique ID"
        ))
    
    # Check edges reference valid nodes
    for i, edge in enumerate(graph.edges):
        if edge.source not in node_id_set:
            errors.append(ValidationError(
                message=f"Edge {i}: source node '{edge.source}' does not exist",
                code="INVALID_EDGE_SOURCE",
                severity="error",
                location=f"edge {i}",
                suggestion=f"Add node '{edge.source}' to your graph or fix the edge"
            ))
        
        if edge.target not in node_id_set:
            errors.append(ValidationError(
                message=f"Edge {i}: target node '{edge.target}' does not exist",
                code="INVALID_EDGE_TARGET",
                severity="error",
                location=f"edge {i}",
                suggestion=f"Add node '{edge.target}' to your graph or fix the edge"
            ))
    
    # Check for duplicate edges (if not multigraph)
    if not graph.multigraph:
        edge_set = set()
        for i, edge in enumerate(graph.edges):
            if graph.directed:
                edge_key = (edge.source, edge.target)
            else:
                # For undirected, (A,B) same as (B,A)
                edge_key = tuple(sorted([edge.source, edge.target]))
            
            if edge_key in edge_set:
                errors.append(ValidationError(
                    message=f"Duplicate edge: {edge.source} → {edge.target}",
                    code="DUPLICATE_EDGE",
                    severity="error",
                    location=f"edge {i}",
                    suggestion="Remove duplicate edges or set multigraph=true"
                ))
            edge_set.add(edge_key)
    
    # Validate edge weights
    if graph.weighted:
        for i, edge in enumerate(graph.edges):
            if edge.weight is None:
                errors.append(ValidationError(
                    message=f"Edge {edge.source} → {edge.target}: weight is missing",
                    code="MISSING_WEIGHT",
                    severity="error",
                    location=f"edge {i}",
                    suggestion="Add a weight value to this edge"
                ))
            elif not isinstance(edge.weight, (int, float)):
                errors.append(ValidationError(
                    message=f"Edge {edge.source} → {edge.target}: weight must be a number",
                    code="INVALID_WEIGHT",
                    severity="error",
                    location=f"edge {i}"
                ))
    
    # Validate capacities and flows (for flow networks)
    for i, edge in enumerate(graph.edges):
        if edge.capacity is not None:
            if not isinstance(edge.capacity, (int, float)) or edge.capacity < 0:
                errors.append(ValidationError(
                    message=f"Edge {edge.source} → {edge.target}: capacity must be non-negative",
                    code="INVALID_CAPACITY",
                    severity="error",
                    location=f"edge {i}"
                ))
        
        if edge.flow is not None:
            if not isinstance(edge.flow, (int, float)) or edge.flow < 0:
                errors.append(ValidationError(
                    message=f"Edge {edge.source} → {edge.target}: flow must be non-negative",
                    code="INVALID_FLOW",
                    severity="error",
                    location=f"edge {i}"
                ))
            
            if edge.capacity is not None and edge.flow > edge.capacity:
                errors.append(ValidationError(
                    message=f"Edge {edge.source} → {edge.target}: flow ({edge.flow}) exceeds capacity ({edge.capacity})",
                    code="FLOW_EXCEEDS_CAPACITY",
                    severity="error",
                    location=f"edge {i}",
                    suggestion="Flow cannot exceed edge capacity"
                ))
    
    return errors


def find_graph_warnings(graph: Graph) -> List[ValidationError]:
    """
    Find potential issues that are warnings (not blocking errors).
    
    Checks:
    - Isolated nodes (no edges)
    - Self-loops
    - Weighted graph with all weights = 1
    - Disconnected components
    """
    warnings = []
    
    if not graph.nodes:
        return warnings
    
    # Build adjacency info
    node_edges = {node.id: [] for node in graph.nodes}
    for edge in graph.edges:
        if edge.source in node_edges:
            node_edges[edge.source].append(edge)
        if edge.target in node_edges and not graph.directed:
            node_edges[edge.target].append(edge)
    
    # Check for isolated nodes
    isolated = [nid for nid, edges in node_edges.items() if not edges]
    if isolated:
        if len(isolated) == 1:
            warnings.append(ValidationError(
                message=f"Node '{isolated[0]}' is isolated (no edges connected)",
                code="ISOLATED_NODE",
                severity="warning",
                suggestion="Is this intentional? Consider connecting it or removing it"
            ))
        else:
            warnings.append(ValidationError(
                message=f"{len(isolated)} nodes are isolated: {', '.join(isolated[:5])}{'...' if len(isolated) > 5 else ''}",
                code="ISOLATED_NODES",
                severity="warning",
                suggestion="These nodes have no edges. Is this intentional?"
            ))
    
    # Check for self-loops
    self_loops = [edge for edge in graph.edges if edge.source == edge.target]
    if self_loops:
        if len(self_loops) == 1:
            warnings.append(ValidationError(
                message=f"Self-loop detected: {self_loops[0].source} → {self_loops[0].source}",
                code="SELF_LOOP",
                severity="warning",
                suggestion="Self-loops are allowed but uncommon. Is this intentional?"
            ))
        else:
            warnings.append(ValidationError(
                message=f"{len(self_loops)} self-loops detected",
                code="SELF_LOOPS",
                severity="warning"
            ))
    
    # Check if weighted graph has all weights = 1 (maybe not intended to be weighted)
    if graph.weighted and graph.edges:
        all_weight_one = all(e.weight == 1.0 or e.weight == 1 for e in graph.edges if e.weight is not None)
        if all_weight_one:
            warnings.append(ValidationError(
                message="All edge weights are 1 - did you mean to have an unweighted graph?",
                code="TRIVIAL_WEIGHTS",
                severity="warning",
                suggestion="Set weighted=false if you don't need weights"
            ))
    
    return warnings


def validate_answer_fields(response: Response, graph: Optional[Graph]) -> List[ValidationError]:
    """
    Validate answer fields in the response.
    
    Checks:
    - Paths reference existing nodes
    - Sets reference existing nodes
    - Edge lists reference existing edges
    """
    errors = []
    
    if not graph or not graph.nodes:
        return errors
    
    node_ids = {node.id for node in graph.nodes}
    
    # Check path fields
    path_fields = [
        ('path', response.path),
        ('cycle', response.cycle),
        ('eulerian_path', response.eulerian_path),
        ('hamiltonian_path', response.hamiltonian_path),
        ('ordering', response.ordering),
        ('topological_order', response.topological_order),
        ('dfs_order', response.dfs_order),
        ('bfs_order', response.bfs_order),
    ]
    
    for field_name, field_value in path_fields:
        if field_value:
            invalid_nodes = [n for n in field_value if n not in node_ids]
            if invalid_nodes:
                errors.append(ValidationError(
                    message=f"{field_name}: references non-existent nodes: {', '.join(invalid_nodes[:5])}",
                    code="INVALID_PATH_NODES",
                    severity="error",
                    location=field_name,
                    suggestion="All nodes in paths must exist in the graph"
                ))
    
    # Check set fields
    set_fields = [
        ('vertex_cover', response.vertex_cover),
        ('independent_set', response.independent_set),
        ('clique', response.clique),
        ('dominating_set', response.dominating_set),
        ('articulation_points', response.articulation_points),
        ('min_cut', response.min_cut),
        ('tree_center', response.tree_center),
    ]
    
    for field_name, field_value in set_fields:
        if field_value:
            invalid_nodes = [n for n in field_value if n not in node_ids]
            if invalid_nodes:
                errors.append(ValidationError(
                    message=f"{field_name}: references non-existent nodes: {', '.join(invalid_nodes[:5])}",
                    code="INVALID_SET_NODES",
                    severity="error",
                    location=field_name
                ))
    
    # Check partitions/components
    if response.partitions:
        for i, partition in enumerate(response.partitions):
            invalid_nodes = [n for n in partition if n not in node_ids]
            if invalid_nodes:
                errors.append(ValidationError(
                    message=f"Partition {i}: references non-existent nodes: {', '.join(invalid_nodes)}",
                    code="INVALID_PARTITION_NODES",
                    severity="error",
                    location=f"partitions[{i}]"
                ))
    
    if response.components:
        for i, component in enumerate(response.components):
            invalid_nodes = [n for n in component if n not in node_ids]
            if invalid_nodes:
                errors.append(ValidationError(
                    message=f"Component {i}: references non-existent nodes: {', '.join(invalid_nodes)}",
                    code="INVALID_COMPONENT_NODES",
                    severity="error",
                    location=f"components[{i}]"
                ))
    
    return errors


# =============================================================================
# FORMATTING FUNCTIONS
# =============================================================================

def format_errors_for_preview(errors: List[ValidationError], max_errors: int = 5) -> str:
    """
    Format validation errors into a human-readable string for preview feedback.
    """
    if not errors:
        return ""
    
    # Separate errors by severity
    critical_errors = [e for e in errors if e.severity == "error"]
    warnings = [e for e in errors if e.severity == "warning"]
    
    lines = []
    
    if critical_errors:
        if len(critical_errors) == 1:
            lines.append("There's an issue with your graph that needs to be fixed:")
        else:
            lines.append(f"There are {len(critical_errors)} issues with your graph that need to be fixed:")
        lines.append("")
        
        for i, err in enumerate(critical_errors[:max_errors], 1):
            lines.append(f"  {i}. {err.message}")
            if err.suggestion:
                lines.append(f"     >> {err.suggestion}")
            lines.append("")
        
        if len(critical_errors) > max_errors:
            lines.append(f"  ... and {len(critical_errors) - max_errors} more issue(s)")
    
    if warnings:
        if lines:
            lines.append("")
        lines.append("Some things to consider (not blocking, but worth checking):")
        lines.append("")
        for i, warn in enumerate(warnings[:max_errors], 1):
            lines.append(f"  - {warn.message}")
            if warn.suggestion:
                lines.append(f"    >> {warn.suggestion}")
        
        if len(warnings) > max_errors:
            lines.append(f"  ... and {len(warnings) - max_errors} more suggestion(s)")
    
    return "\n".join(lines)


def errors_to_dict_list(errors: List[ValidationError]) -> List[Dict]:
    """Convert ValidationError objects to dictionaries for JSON serialization."""
    return [
        {
            "message": e.message,
            "code": e.code,
            "severity": e.severity,
            "location": e.location,
            "suggestion": e.suggestion
        }
        for e in errors
    ]


def get_structured_graph_info(graph: Graph) -> Dict[str, Any]:
    """
    Extract structured information about a graph.
    
    Returns a dictionary with graph properties, counts, and metadata
    for programmatic use.
    """
    # Build adjacency info for analysis
    node_edges = {node.id: [] for node in graph.nodes}
    for edge in graph.edges:
        if edge.source in node_edges:
            node_edges[edge.source].append(edge)
        if edge.target in node_edges and not graph.directed:
            node_edges[edge.target].append(edge)
    
    # Find isolated nodes
    isolated_nodes = [nid for nid, edges in node_edges.items() if not edges]
    
    # Check for self-loops
    has_self_loops = any(edge.source == edge.target for edge in graph.edges)
    num_self_loops = sum(1 for edge in graph.edges if edge.source == edge.target)
    
    # Degree information
    if graph.directed:
        in_degrees = {node.id: 0 for node in graph.nodes}
        out_degrees = {node.id: 0 for node in graph.nodes}
        for edge in graph.edges:
            if edge.source in out_degrees:
                out_degrees[edge.source] += 1
            if edge.target in in_degrees:
                in_degrees[edge.target] += 1
        
        degree_info = {
            "max_in_degree": max(in_degrees.values()) if in_degrees else 0,
            "max_out_degree": max(out_degrees.values()) if out_degrees else 0,
            "avg_in_degree": sum(in_degrees.values()) / len(in_degrees) if in_degrees else 0,
            "avg_out_degree": sum(out_degrees.values()) / len(out_degrees) if out_degrees else 0,
        }
    else:
        degrees = {node.id: len(edges) for node.id, edges in node_edges.items()}
        degree_info = {
            "max_degree": max(degrees.values()) if degrees else 0,
            "min_degree": min(degrees.values()) if degrees else 0,
            "avg_degree": sum(degrees.values()) / len(degrees) if degrees else 0,
        }
    
    # Weight information (if weighted)
    weight_info = {}
    if graph.weighted and graph.edges:
        weights = [e.weight for e in graph.edges if e.weight is not None]
        if weights:
            weight_info = {
                "min_weight": min(weights),
                "max_weight": max(weights),
                "avg_weight": sum(weights) / len(weights),
                "total_weight": sum(weights),
            }
    
    # Capacity/flow information (if present)
    flow_info = {}
    capacities = [e.capacity for e in graph.edges if e.capacity is not None]
    flows = [e.flow for e in graph.edges if e.flow is not None]
    if capacities:
        flow_info["has_capacities"] = True
        flow_info["total_capacity"] = sum(capacities)
    if flows:
        flow_info["has_flows"] = True
        flow_info["total_flow"] = sum(flows)
    
    return {
        "directed": graph.directed,
        "weighted": graph.weighted,
        "multigraph": graph.multigraph,
        "num_nodes": len(graph.nodes),
        "num_edges": len(graph.edges),
        "isolated_nodes": isolated_nodes,
        "has_self_loops": has_self_loops,
        "num_self_loops": num_self_loops,
        "degree_info": degree_info,
        "weight_info": weight_info,
        "flow_info": flow_info,
        "graph_name": graph.name,
    }


def format_graph_text(graph: Graph) -> str:
    """Format a graph as readable text."""
    lines = []
    
    # Graph properties
    graph_type = "Directed" if graph.directed else "Undirected"
    weighted = " Weighted" if graph.weighted else ""
    lines.append(f"{graph_type}{weighted} Graph")
    
    if graph.name:
        lines.append(f"Name: {graph.name}")
    
    # Nodes
    lines.append(f"\nNodes ({len(graph.nodes)}):")
    for node in graph.nodes:
        node_info = f"  {node.id}"
        if node.label and node.label != node.id:
            node_info += f" (label: {node.label})"
        if node.partition is not None:
            node_info += f" [partition {node.partition}]"
        if node.color is not None:
            node_info += f" [color {node.color}]"
        if node.weight is not None:
            node_info += f" [weight {node.weight}]"
        lines.append(node_info)
    
    # Edges
    lines.append(f"\nEdges ({len(graph.edges)}):")
    for edge in graph.edges:
        arrow = " → " if graph.directed else " — "
        edge_info = f"  {edge.source}{arrow}{edge.target}"
        if edge.weight and edge.weight != 1.0:
            edge_info += f" (weight: {edge.weight})"
        if edge.capacity is not None:
            edge_info += f" (capacity: {edge.capacity})"
        if edge.flow is not None:
            edge_info += f" (flow: {edge.flow})"
        lines.append(edge_info)
    
    return "\n".join(lines)


def format_graph_latex(graph: Graph) -> str:
    """Format a graph as LaTeX representation."""
    lines = []
    
    # Graph description
    graph_type = "\\text{Directed}" if graph.directed else "\\text{Undirected}"
    weighted = "\\text{ Weighted}" if graph.weighted else ""
    lines.append(f"{graph_type}{weighted}")
    
    # Nodes in set notation
    node_ids = ", ".join([f"{node.id}" for node in graph.nodes])
    lines.append(f"V = \\{{{node_ids}\\}}")
    
    # Edges in set notation
    if graph.edges:
        arrow = "\\to" if graph.directed else "-"
        edge_list = []
        for edge in graph.edges:
            if edge.weight and edge.weight != 1.0:
                edge_list.append(f"({edge.source} {arrow} {edge.target}, {edge.weight})")
            else:
                edge_list.append(f"{edge.source} {arrow} {edge.target}")
        edges_str = ", ".join(edge_list)
        lines.append(f"E = \\{{{edges_str}\\}}")
    else:
        lines.append(f"E = \\emptyset")
    
    return "\\\\".join(lines)


def format_answer_text(response: Response) -> str:
    """Format student answers as readable text."""
    lines = []
    
    # Boolean answers
    bool_fields = [
        ("is_connected", "Connected"),
        ("is_bipartite", "Bipartite"),
        ("is_tree", "Tree"),
        ("is_planar", "Planar"),
        ("has_cycle", "Has Cycle"),
        ("is_dag", "DAG"),
        ("has_eulerian_path", "Has Eulerian Path"),
        ("has_eulerian_circuit", "Has Eulerian Circuit"),
        ("has_hamiltonian_path", "Has Hamiltonian Path"),
        ("has_hamiltonian_circuit", "Has Hamiltonian Circuit"),
    ]
    
    for field, label in bool_fields:
        value = getattr(response, field, None)
        if value is not None:
            lines.append(f"{label}: {'Yes' if value else 'No'}")
    
    # Path answers
    path_fields = [
        ("path", "Path"),
        ("cycle", "Cycle"),
        ("eulerian_path", "Eulerian Path"),
        ("hamiltonian_path", "Hamiltonian Path"),
        ("ordering", "Ordering"),
        ("dfs_order", "DFS Order"),
        ("bfs_order", "BFS Order"),
        ("topological_order", "Topological Order"),
    ]
    
    for field, label in path_fields:
        value = getattr(response, field, None)
        if value is not None:
            lines.append(f"{label}: {' → '.join(value)}")
    
    # Numeric answers
    numeric_fields = [
        ("distance", "Distance"),
        ("flow_value", "Max Flow"),
        ("chromatic_number", "Chromatic Number"),
        ("num_components", "Number of Components"),
        ("mst_weight", "MST Weight"),
        ("diameter", "Diameter"),
        ("girth", "Girth"),
    ]
    
    for field, label in numeric_fields:
        value = getattr(response, field, None)
        if value is not None:
            lines.append(f"{label}: {value}")
    
    # Set answers
    if response.partitions:
        parts = " | ".join(["{" + ", ".join(p) + "}" for p in response.partitions])
        lines.append(f"Partitions: {parts}")
    
    if response.components:
        comps = " | ".join(["{" + ", ".join(c) + "}" for c in response.components])
        lines.append(f"Components: {comps}")
    
    if response.coloring:
        colors = ", ".join([f"{node}:{color}" for node, color in response.coloring.items()])
        lines.append(f"Coloring: {{{colors}}}")
    
    if response.matching:
        matches = ", ".join([f"({u},{v})" for u, v in response.matching])
        lines.append(f"Matching: {{{matches}}}")
    
    if response.vertex_cover:
        lines.append(f"Vertex Cover: {{{', '.join(response.vertex_cover)}}}")
    
    if response.independent_set:
        lines.append(f"Independent Set: {{{', '.join(response.independent_set)}}}")
    
    if response.clique:
        lines.append(f"Clique: {{{', '.join(response.clique)}}}")
    
    if response.articulation_points:
        lines.append(f"Articulation Points: {{{', '.join(response.articulation_points)}}}")
    
    if response.degree_sequence:
        lines.append(f"Degree Sequence: [{', '.join(map(str, response.degree_sequence))}]")
    
    if response.spanning_tree or response.mst:
        edges = response.spanning_tree or response.mst
        edge_strs = [f"{e.source}-{e.target}" for e in edges]
        lines.append(f"Tree Edges: {{{', '.join(edge_strs)}}}")
    
    return "\n".join(lines)


# =============================================================================
# MAIN PREVIEW FUNCTION
# =============================================================================

def preview_function(response: Any, params: Params) -> Result:
    """
    Validate a student's graph response before submission.
    
    This function performs structural validation to catch clear errors early,
    preventing students from submitting obviously invalid graphs for evaluation.
    
    Args:
        response: Student's response (graph + answers)
        params: Extra parameters:
            - show_warnings (bool): Whether to show warnings (default: True)
            - validate_answers (bool): Whether to validate answer fields (default: True)
    
    Returns:
        Result with:
        - preview.latex: Graph summary if valid
        - preview.feedback: Error/warning messages if any
        - preview.sympy: Formatted graph + structured validation data
    """
    # Extract params with defaults
    show_warnings = True
    validate_answers = True
    
    if hasattr(params, 'get'):
        show_warnings = params.get("show_warnings", True)
        validate_answers = params.get("validate_answers", True)
    elif isinstance(params, dict):
        show_warnings = params.get("show_warnings", True)
        validate_answers = params.get("validate_answers", True)
    
    # Handle empty response
    if not response:
        return Result(
            preview=Preview(
                feedback="No response provided! Please build your graph or enter your answer.",
                sympy={
                    "valid": False,
                    "parse_error": True,
                    "errors": [{
                        "message": "No response provided",
                        "code": "NO_RESPONSE",
                        "severity": "error"
                    }]
                }
            )
        )
    
    try:
        # Step 1: Parse the response
        response_obj = parse_graph_response(response)
        
    except Exception as e:
        # Failed to parse - this is a critical error
        error_msg = str(e)
        
        # Make error message more user-friendly
        if "validation error" in error_msg.lower():
            if "nodes" in error_msg.lower():
                feedback = "Your graph is missing the 'nodes' list. Every graph needs nodes!"
                error_code = "MISSING_NODES"
            elif "edges" in error_msg.lower():
                feedback = "There's an issue with your edges. Each edge needs source and target nodes."
                error_code = "INVALID_EDGES"
            elif "directed" in error_msg.lower():
                feedback = "Your graph needs to specify if it's directed (true/false)."
                error_code = "MISSING_DIRECTED"
            else:
                feedback = f"Your graph structure isn't quite right. Check your JSON format."
                error_code = "INVALID_STRUCTURE"
        elif "json" in error_msg.lower():
            feedback = "Couldn't read your data. Make sure it's properly formatted JSON."
            error_code = "INVALID_JSON"
        elif "no response" in error_msg.lower():
            feedback = "No response provided! Please build your graph before checking."
            error_code = "NO_RESPONSE"
        else:
            feedback = f"There's a problem with your format: {error_msg}"
            error_code = "PARSE_ERROR"
        
        return Result(
            preview=Preview(
                feedback=feedback,
                sympy={
                    "valid": False,
                    "parse_error": True,
                    "errors": [{
                        "message": error_msg,
                        "code": error_code,
                        "severity": "error"
                    }]
                }
            )
        )
    
    # Step 2: Validate graph structure if present
    all_errors: List[ValidationError] = []
    warnings: List[ValidationError] = []
    
    if response_obj.graph:
        # Run structural validation
        structural_errors = validate_graph_structure(response_obj.graph)
        all_errors.extend(structural_errors)
        
        # If there are structural errors, don't proceed with other checks
        if structural_errors:
            feedback = "Your graph has some issues that need to be fixed before submission.\n\n"
            feedback += format_errors_for_preview(all_errors)
            
            # Build structured output with basic info
            sympy_output = {
                "valid": False,
                "errors": errors_to_dict_list(all_errors),
                "num_nodes": len(response_obj.graph.nodes),
                "num_edges": len(response_obj.graph.edges),
            }
            
            return Result(
                preview=Preview(
                    feedback=feedback,
                    sympy=sympy_output
                )
            )
        
        # Check for warnings
        if show_warnings:
            graph_warnings = find_graph_warnings(response_obj.graph)
            warnings.extend(graph_warnings)
        
        # Validate answer fields reference valid nodes
        if validate_answers:
            answer_errors = validate_answer_fields(response_obj, response_obj.graph)
            all_errors.extend(answer_errors)
    
    # Step 3: Check if there are critical errors
    has_errors = len(all_errors) > 0
    has_warnings = len(warnings) > 0
    
    if has_errors:
        # Critical errors - cannot submit
        feedback = "Hold on! Your response has issues that need to be addressed.\n\n"
        feedback += format_errors_for_preview(all_errors + warnings)
        
        # Build structured output
        sympy_output = {
            "valid": False,
            "errors": errors_to_dict_list(all_errors),
            "warnings": errors_to_dict_list(warnings),
        }
        
        # Add graph info if present
        if response_obj.graph:
            graph_info = get_structured_graph_info(response_obj.graph)
            sympy_output.update(graph_info)
        
        return Result(
            preview=Preview(
                feedback=feedback,
                sympy=sympy_output
            )
        )
    
    # Step 4: Build success preview with structured output
    latex_parts = []
    
    # Build structured JSON output
    sympy_output = {
        "valid": True,
        "errors": [],
        "warnings": errors_to_dict_list(warnings),
    }
    
    # Format the graph if present
    if response_obj.graph:
        latex_parts.append(format_graph_latex(response_obj.graph))
        
        # Add graph summary
        graph = response_obj.graph
        graph_type = "Directed" if graph.directed else "Undirected"
        if graph.weighted:
            graph_type += " Weighted"
        
        node_word = "node" if len(graph.nodes) == 1 else "nodes"
        edge_word = "edge" if len(graph.edges) == 1 else "edges"
        summary = f"{graph_type} graph with {len(graph.nodes)} {node_word} and {len(graph.edges)} {edge_word}"
        
        # Add structured graph info to sympy output
        graph_info = get_structured_graph_info(response_obj.graph)
        sympy_output.update(graph_info)
    else:
        summary = "Answer (no graph)"
    
    # Build feedback message
    if has_warnings:
        # Valid but with warnings
        warning_feedback = format_errors_for_preview(warnings)
        feedback = f"Looking good! Your response is structurally valid.\n\n"
        feedback += f"Summary: {summary}\n\n"
        feedback += warning_feedback
    else:
        feedback = f"Great! Your response is structurally valid and ready for submission.\n\n"
        feedback += f"Summary: {summary}"
    
    # Set latex output
    latex_output = "\\\\".join(latex_parts) if latex_parts else summary
    
    return Result(
        preview=Preview(
            latex=latex_output,
            feedback=feedback,
            sympy=sympy_output
        )
    )
