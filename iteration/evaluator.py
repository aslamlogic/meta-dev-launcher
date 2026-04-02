import requests


def evaluate_system(spec: dict, base_url: str) -> dict:
    """
    Deterministic evaluator.

    Validates:
    1. System existence (must have endpoints)
    2. Endpoint reachability
    3. Basic response validity
    """

    endpoints = spec.get("api", {}).get("endpoints", [])

    # ---- HARD RULE: EMPTY SYSTEM = FAILURE ----
    if not endpoints:
        return {
            "status": "failure",
            "goal_satisfied": False,
            "reason": "no endpoints defined",
            "base_url": base_url,
            "checked_endpoints": 0,
            "failing_endpoints": ["GET /health"],
            "results": []
        }

    results = []
    failing = []

    for ep in endpoints:
        method = ep.get("method", "GET").upper()
        path = ep.get("path", "/")

        url = f"{base_url}{path}"

        try:
            if method == "GET":
                response = requests.get(url)
            elif method == "POST":
                response = requests.post(url, json={})
            else:
                results.append({
                    "endpoint": f"{method} {path}",
                    "status": "skipped",
                    "reason": "unsupported method"
                })
                continue

            if response.status_code >= 400:
                failing.append(f"{method} {path}")
                results.append({
                    "endpoint": f"{method} {path}",
                    "status": "fail",
                    "code": response.status_code
                })
            else:
                results.append({
                    "endpoint": f"{method} {path}",
                    "status": "pass",
                    "code": response.status_code
                })

        except Exception as e:
            failing.append(f"{method} {path}")
            results.append({
                "endpoint": f"{method} {path}",
                "status": "error",
                "error": str(e)
            })

    return {
        "status": "success" if not failing else "failure",
        "goal_satisfied": not failing,
        "base_url": base_url,
        "checked_endpoints": len(endpoints),
        "failing_endpoints": failing,
        "results": results
    }
