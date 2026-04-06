# iteration/evaluator.py

from fastapi.testclient import TestClient


def evaluate_system(app, spec):
    result = {
        "status": "failure",
        "logs": [],
        "failing_endpoints": [],
        "schema_mismatches": []
    }

    try:
        client = TestClient(app)

        # Basic health check
        response = client.get("/health")

        if response.status_code != 200:
            result["logs"].append(f"Health check failed: {response.status_code}")
            return result

        data = response.json()

        if data.get("status") != "ok":
            result["logs"].append("Health endpoint returned invalid response")
            return result

        # If we reach here → pass
        result["status"] = "success"
        return result

    except Exception as e:
        result["logs"].append(f"EVAL_ERROR: {str(e)}")
        return result
