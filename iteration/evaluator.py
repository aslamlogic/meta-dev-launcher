from fastapi.testclient import TestClient


def evaluate_system(app, spec: dict):
    """
    Evaluates generated FastAPI app against spec.
    """

    results = {
        "status": "success",
        "logs": [],
        "failing_endpoints": [],
        "schema_mismatches": []
    }

    try:
        # IMPORTANT
