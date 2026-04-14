from fastapi.testclient import TestClient
from typing import Dict, Any
import traceback


VALID_HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}


# ============================================================
# NORMALISATION LAYER (CRITICAL FIX)
# ============================================================

def normalize_endpoint_spec(endpoint: Dict[str, Any]) -> Dict[str, Any]:
    method = str(endpoint.get("method", "")).strip().upper()
    path = str(endpoint.get("path", "")).strip()

    # Fix schema placeholders
    if method in ["STRING", "", "NONE"]:
        method = "GET"

    if path in ["string", "", "NONE"]:
        path = "/health"

    if not path.startswith("/"):
        path = "/" + path

    return {
        "method": method,
        "path": path
    }


def normalize_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    endpoints = spec.get("endpoints", [])
    spec["endpoints"] = [normalize_endpoint_spec(e) for e in endpoints]
    return spec


# ============================================================
# MAIN ENTRYPOINT (MATCHES CONTROLLER EXPECTATION)
# ============================================================

def evaluate_app(app, spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    This MUST exist — controller imports this exact name.
    """

    try:
        spec = normalize_spec(spec)

        client = TestClient(app)

        failing_endpoints = []
        logs = []

        for endpoint in spec.get("endpoints", []):
            method = endpoint["method"]
            path = endpoint["path"]

            # ---------------------------
            # METHOD VALIDATION
            # ---------------------------
            if method not in VALID_HTTP_METHODS:
                failing_endpoints.append({
                    "method": method,
                    "path": path,
                    "reason": "unsupported_method"
                })
                logs.append(f"{method} {path} → FAIL (unsupported method)")
                continue

            # ---------------------------
            # RUNTIME TEST
            # ---------------------------
            try:
                response = client.request(method, path)

                if response.status_code >= 400:
                    failing_endpoints.append({
                        "method": method,
                        "path": path,
                        "reason": f"http_{response.status_code}"
                    })
                    logs.append(f"{method} {path} → FAIL ({response.status_code})")
                else:
                    logs.append(f"{method} {path} → PASS")

            except Exception as e:
                failing_endpoints.append({
                    "method": method,
                    "path": path,
                    "reason": "runtime_error"
                })
                logs.append(f"{method} {path} → FAIL (runtime error: {str(e)})")

        if failing_endpoints:
            return {
                "status": "failure",
                "logs": logs,
                "failing_endpoints": failing_endpoints,
                "schema_mismatches": []
            }

        return {
            "status": "success",
            "logs": logs,
            "failing_endpoints": [],
            "schema_mismatches": []
        }

    except Exception as e:
        return {
            "status": "failure",
            "logs": [f"CRITICAL ERROR: {str(e)}", traceback.format_exc()],
            "failing_endpoints": [],
            "schema_mismatches": []
        }
