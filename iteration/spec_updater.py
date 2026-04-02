from copy import deepcopy


WRITE_METHODS = {"POST", "PUT", "PATCH"}


def _ensure_api_root(spec: dict) -> None:
    if "api" not in spec or not isinstance(spec["api"], dict):
        spec["api"] = {}
    if "endpoints" not in spec["api"] or not isinstance(spec["api"]["endpoints"], list):
        spec["api"]["endpoints"] = []


def _parse_endpoint_string(value: str):
    parts = value.strip().split(maxsplit=1)
    if len(parts) != 2:
        raise ValueError(f"Invalid endpoint format: {value}")
    return parts[0].upper(), parts[1].strip()


def _find_endpoint(endpoints, method, path):
    for ep in endpoints:
        if ep.get("method") == method and ep.get("path") == path:
            return ep
    return None


def _default_endpoint(method, path):
    return {
        "method": method,
        "path": path,
        "request_schema": {} if method in WRITE_METHODS else None,
        "response_schema": {"status": "string"},
    }


def _apply_missing_endpoints(spec, evaluation):
    endpoints = spec["api"]["endpoints"]

    for item in evaluation.get("failing_endpoints", []):
        method, path = _parse_endpoint_string(item)
        if not _find_endpoint(endpoints, method, path):
            endpoints.append(_default_endpoint(method, path))


def _apply_schema_mismatches(spec, evaluation):
    endpoints = spec["api"]["endpoints"]

    for item in evaluation.get("schema_mismatches", []):
        method = item.get("method")
        path = item.get("path")
        actual = item.get("actual_response")

        if not method or not path:
            continue

        ep = _find_endpoint(endpoints, method, path)

        if not ep:
            ep = _default_endpoint(method, path)
            endpoints.append(ep)

        ep["response_schema"] = actual


def _apply_post_failures(spec, evaluation):
    endpoints = spec["api"]["endpoints"]

    for item in evaluation.get("post_failures", []):
        method = item.get("method")
        path = item.get("path")

        if method != "POST":
            continue

        ep = _find_endpoint(endpoints, method, path)

        if not ep:
            ep = _default_endpoint(method, path)
            endpoints.append(ep)

        if not ep.get("request_schema"):
            ep["request_schema"] = {}


def update_spec(spec: dict, evaluation: dict) -> dict:
    updated = deepcopy(spec)
    _ensure_api_root(updated)

    _apply_missing_endpoints(updated, evaluation)
    _apply_schema_mismatches(updated, evaluation)
    _apply_post_failures(updated, evaluation)

    return updated
