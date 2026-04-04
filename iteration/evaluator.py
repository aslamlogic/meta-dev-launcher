import importlib
import sys
from typing import Any, Dict, List
from fastapi.testclient import TestClient
from iteration.schema_validator import validate_json_schema


def _reload_generated_app():
    # Remove ALL cached modules under generated_app
    modules_to_delete = [m for m in sys.modules if m.startswith("generated_app")]
    for m in modules_to_delete:
        del sys.modules[m]
    
    # Fresh import
    import generated_app.main
    importlib.reload(generated_app.main)
    
    from generated_app.main import app
    return app


def evaluate_system(spec: Dict[str, Any]) -> Dict[str, Any]:
    logs = []
    failing_endpoints = []
    schema_mismatches = []

    try:
        app = _reload_generated_app()
        client = TestClient(app)
        logs.append("App loaded cleanly")
    except Exception as e:
        return {
            "status": "failure",
            "logs": [str(e)],
            "failing_endpoints": [],
            "schema_mismatches": [{"issue": "import_failed", "details": str(e)}],
        }

    for ep in spec.get("endpoints", []):
        method = ep.get("method", "GET").upper()
        path = ep.get("path")
        expected = ep.get("expected_response", {})

        try:
            if method == "GET":
                r = client.get(path)
            elif method == "POST":
                r = client.post(path)
            elif method == "PUT":
                r = client.put(path)
            elif method == "DELETE":
                r = client.delete(path)
            else:
                raise ValueError("bad method")
        except Exception as e:
            failing_endpoints.append(path)
            schema_mismatches.append({"issue": "call_failed", "details": str(e)})
            continue

        if r.status_code >= 400:
            failing_endpoints.append(path)
            schema_mismatches.append({"issue": "http_error", "status": r.status_code})
            continue

        try:
            data = r.json()
        except Exception:
            failing_endpoints.append(path)
            schema_mismatches.append({"issue": "invalid_json"})
            continue

        mismatches = validate_json_schema(expected, data)

        if mismatches:
            failing_endpoints.append(path)
            schema_mismatches.append({"issue": "schema", "mismatches": mismatches})

    success = not failing_endpoints and not schema_mismatches

    return {
        "status": "success" if success else "failure",
        "logs": logs,
        "failing_endpoints": failing_endpoints,
        "schema_mismatches": schema_mismatches,
    }
