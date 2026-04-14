from fastapi.testclient import TestClient


def evaluate_system(app, spec: dict):
    """
    Strict evaluation:
    - Endpoint must exist
    - Must return 2xx ONLY to pass
    """

    results = {
        "status": "success",
        "logs": [],
        "failing_endpoints": [],
        "schema_mismatches": []
    }

    try:
        client = TestClient(app)

        endpoints = spec.get("endpoints", [])

        for ep in endpoints:
            method = ep.get("method", "GET").upper()
            path = ep.get("path")

            try:
                if method == "GET":
                    response = client.get(path)
                elif method == "POST":
                    response = client.post(path, json={})
                else:
                    results["logs"].append(f"Unsupported method: {method}")
                    continue

                # STRICT CHECK
                if response.status_code != 200:
                    results["status"] = "failure"
                    results["failing_endpoints"].append(f"{method} {path}")
                    results["logs"].append(
                        f"{method} {path} → {response.status_code} (FAIL)"
                    )
                else:
                    results["logs"].append(
                        f"{method} {path} → 200 (OK)"
                    )

            except Exception as e:
                results["status"] = "failure"
                results["failing_endpoints"].append(f"{method} {path}")
                results["logs"].append(f"{method} {path} → EXCEPTION: {str(e)}")

        return results

    except Exception as e:
        return {
            "status": "failure",
            "logs": [f"EVAL_ERROR: {str(e)}"],
            "failing_endpoints": [],
            "schema_mismatches": []
        }
