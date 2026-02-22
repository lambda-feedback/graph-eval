"""
FastAPI endpoint for local testing of graph evaluation function.

This provides a REST API for testing the evaluation function locally
before deploying to Lambda Feedback.

Run with:
    uvicorn evaluation_function.api:app --reload

Then test at:
    http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Any
from pydantic import BaseModel

from .schemas.graph import Graph
from .schemas.request import Response, Answer
from .schemas.params import EvaluationParams
from lf_toolkit.evaluation import Result as LFResult, Params
from .evaluation import evaluation_function
from .preview import preview_function

app = FastAPI(
    title="Graph Evaluation API",
    description="API for evaluating student graph theory responses",
    version="1.0.0"
)

# -----------------------------
# CORS Setup: allow all origins
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


# -----------------------------
# Request/Response Schemas
# -----------------------------

class EvaluationRequest(BaseModel):
    """
    Payload sent from frontend for evaluation.

    response: Student's graph/answer (dict or JSON string)
    answer: Expected correct answer (dict or JSON string)
    params: Evaluation parameters
    """
    response: Any
    answer: Any
    params: Params


class PreviewRequest(BaseModel):
    """
    Payload sent from frontend for preview.

    response: Student's graph/answer (dict or JSON string)
    params: Preview parameters (optional)
    """
    response: Any
    params: Params = None


# -----------------------------
# Helper: parse graph response
# -----------------------------

def validate_graph_response(value: str | dict) -> Response:
    """
    Parse a graph response from string or dict into the Response model.
    """
    if isinstance(value, str):
        return Response.model_validate_json(value)
    return Response.model_validate(value)


def validate_graph_answer(value: str | dict) -> Answer:
    """
    Parse an answer from string or dict into the Answer model.
    """
    if isinstance(value, str):
        return Answer.model_validate_json(value)
    return Answer.model_validate(value)


# -----------------------------
# API Endpoints
# -----------------------------

@app.get("/")
def root():
    """
    Root endpoint - API information.
    """
    return {
        "name": "Graph Evaluation API",
        "version": "1.0.0",
        "endpoints": {
            "evaluate": "/evaluate/graph",
            "preview": "/preview/graph",
            "docs": "/docs",
            "health": "/health"
        }
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "service": "graph-eval"}


@app.post("/evaluate/graph")
def evaluate_graph(payload: EvaluationRequest):
    """
    Evaluate a student's graph response against the expected answer.
    
    Returns detailed evaluation result with feedback.
    
    Example request:
    ```json
    {
      "response": {
        "graph": {
          "nodes": [{"id": "A"}, {"id": "B"}],
          "edges": [{"source": "A", "target": "B"}],
          "directed": false
        },
        "is_connected": true
      },
      "answer": {
        "is_connected": true
      },
      "params": {
        "evaluation_type": "connectivity",
        "feedback_level": "standard"
      }
    }
    ```
    """
    try:
        # Parse student response and expected answer
        student_response = validate_graph_response(payload.response)
        expected_answer = validate_graph_answer(payload.answer)
        
        # Call the evaluation function
        result = evaluation_function(
            response=student_response,
            answer=expected_answer,
            params=payload.params
        )
        
        # Return the result
        return {
            "is_correct": result.get("is_correct", False),
            "feedback": result.get("feedback", ""),
            "evaluation_details": result.get("evaluation_details"),
            "visualization": result.get("visualization"),
            "input_data": {
                "response": student_response.model_dump(),
                "answer": expected_answer.model_dump()
            }
        }

    except Exception as e:
        # Return structured HTTP error with input data
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Evaluation failed",
                "message": str(e),
                "type": type(e).__name__,
                "received": {
                    "response": payload.response,
                    "answer": payload.answer,
                    "params": payload.params,
                },
            },
        )


@app.post("/preview/graph")
def preview_graph(payload: PreviewRequest):
    """
    Preview and validate a student's graph response before submission.
    
    This performs structural validation and returns formatted preview.
    
    Example request:
    ```json
    {
      "response": {
        "graph": {
          "nodes": [{"id": "A"}, {"id": "B"}, {"id": "C"}],
          "edges": [
            {"source": "A", "target": "B", "weight": 5},
            {"source": "B", "target": "C", "weight": 3}
          ],
          "directed": false,
          "weighted": true
        }
      },
      "params": {
        "show_warnings": true,
        "validate_answers": true
      }
    }
    ```
    """
    try:
        # Call the preview function
        params = payload.params if payload.params else Params()
        result = preview_function(
            response=payload.response,
            params=params
        )
        
        # Return the preview result
        preview = result.get("preview", {})
        return {
            "preview": {
                "latex": preview.get("latex", ""),
                "sympy": preview.get("sympy", ""),
                "feedback": preview.get("feedback", "")
            }
        }

    except Exception as e:
        # Return structured HTTP error
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Preview failed",
                "message": str(e),
                "type": type(e).__name__,
                "received": {
                    "response": payload.response,
                    "params": payload.params,
                },
            },
        )


@app.post("/validate/graph")
def validate_graph(payload: PreviewRequest):
    """
    Validate graph structure without full evaluation.
    
    Returns validation errors and warnings only.
    """
    try:
        from .preview import validate_graph_structure, find_graph_warnings, validate_answer_fields
        
        # Parse the response
        response_obj = validate_graph_response(payload.response)
        
        if not response_obj.graph:
            return {
                "valid": False,
                "errors": [],
                "warnings": [],
                "message": "No graph provided"
            }
        
        # Run validations
        errors = validate_graph_structure(response_obj.graph)
        warnings = find_graph_warnings(response_obj.graph)
        answer_errors = validate_answer_fields(response_obj, response_obj.graph)
        
        all_errors = errors + answer_errors
        
        return {
            "valid": len(all_errors) == 0,
            "errors": [
                {
                    "message": e.message,
                    "code": e.code,
                    "severity": e.severity,
                    "location": e.location,
                    "suggestion": e.suggestion
                }
                for e in all_errors
            ],
            "warnings": [
                {
                    "message": w.message,
                    "code": w.code,
                    "severity": w.severity,
                    "suggestion": w.suggestion
                }
                for w in warnings
            ],
            "graph_info": {
                "num_nodes": len(response_obj.graph.nodes),
                "num_edges": len(response_obj.graph.edges),
                "directed": response_obj.graph.directed,
                "weighted": response_obj.graph.weighted
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Validation failed",
                "message": str(e),
                "type": type(e).__name__
            }
        )


# -----------------------------
# Run with: uvicorn evaluation_function.api:app --reload
# -----------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
