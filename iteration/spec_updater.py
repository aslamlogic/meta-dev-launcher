def update_spec_with_failures(spec, evaluation):
    """
    Deterministic correction injection.
    This is where system LEARNS from failure.
    """

    if "constraints" not in spec:
        spec["constraints"] = []

    logs = evaluation.get("logs", [])

    # ============================================================
    # CRITICAL FIX: APP CONTRACT ENFORCEMENT
    # ============================================================
    for log in logs:

        if "app_not_callable" in log:

            constraint = {
                "type": "hard_requirement",
                "rule": "application_must_be_fastapi",
                "instruction": (
                    "The generated application MUST define:\n"
                    "from fastapi import FastAPI\n"
                    "app = FastAPI()\n"
                    "AND must expose 'app' as the ASGI callable.\n"
                    "DO NOT return dictionaries or non-callable objects."
                )
            }

            if constraint not in spec["constraints"]:
                spec["constraints"].append(constraint)

        if "unsupported_method" in log:

            constraint = {
                "type": "hard_requirement",
                "rule": "valid_http_methods",
                "instruction": (
                    "All endpoints MUST use valid HTTP methods: "
                    "GET, POST, PUT, DELETE, PATCH."
                )
            }

            if constraint not in spec["constraints"]:
                spec["constraints"].append(constraint)

        if "http_404" in log:

            constraint = {
                "type": "hard_requirement",
                "rule": "required_health_endpoint",
                "instruction": (
                    "Application MUST implement endpoint:\n"
                    "GET /health\n"
                    "return {'status': 'ok'}"
                )
            }

            if constraint not in spec["constraints"]:
                spec["constraints"].append(constraint)

    return spec
