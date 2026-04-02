import json
import os
import sys
from pathlib import Path
from typing import Any

import requests

SPEC_CANDIDATES = [
    Path("specs/init.json"),
    Path("specs/app.json"),
]


def fail(message: str) -> None:
    print(json.dumps({"status": "error", "message": message}, indent=2))
    sys.exit(1)


def read_spec() -> tuple[Path, dict]:
    for path in SPEC_CANDIDATES:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return path, json.load(f)
    fail("No spec found. Expected specs/init.json or specs/app.json.")


def get_base_url() -> str:
    if len(sys.argv) > 1 and sys.argv[1].strip():
        return sys.argv[1].rstrip("/")
    env_url = os.getenv("DEPLOYED_URL", "").strip()
    if env_url:
        return env_url.rstrip("/")
    fail("No deployed URL provided. Pass URL as first argument or set DEPLOYED_URL.")


def make_dummy_payload(schema: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for key, declared_type in schema.items():
        if declared_type == "string":
            payload[key] = "test"
        elif declared_type == "integer":
            payload[key] = 1
        elif declared_type == "number":
            payload[key] = 1.0
        elif declared_type == "boolean":
            payload[key] = True
        elif declared_type == "object":
            payload[key] = {}
        elif declared_type == "array":
            payload[key] = []
        else:
            payload[key] = "test"
    return payload


def validate_response_schema(data: Any, schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return ["Response is not a JSON object"]

    for key, declared_type in schema.items():
        if key not in data:
            errors.append(f"Missing key: {key}")
            continue

        value = data[key]

        if declared_type == "string" and not isinstance(value, str):
            errors.append(f"Key {key} is not string")
        elif declared_type == "integer" and not isinstance(value, int):
            errors.append(f"Key {key} is not integer")
        elif declared_type == "number" and not isinstance(value, (int, float)):
            errors.append(f"Key {key} is not number")
        elif declared_type == "boolean" and not isinstance(value, bool):
            errors.append(f"Key {key} is not boolean")
        elif declared_type == "object" and not isinstance(value, dict):
            errors.append(f"Key {key} is not object")
        elif declared_type == "array" and not isinstance(value, list):
            errors.append(f"Key {key} is not array")

    return errors


def evaluate_endpoint(base_url: str, endpoint: dict[str, Any]) -> dict[str, Any]:
    method = str(endpoint.get("method", "")).upper()
    path = endpoint.get("path")
    response_schema = endpoint.get("response", {}).get("schema", {})

    if not method or not path:
        return {
            "ok": False,
            "endpoint": f"{method} {path}",
            "error": "Endpoint missing method or path in spec",
        }

    url = f"{base_url}{path}"

    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            request_schema = endpoint.get("request", {}).get("schema", {})
            payload = make_dummy_payload(request_schema)
            response = requests.post(url, json=payload, timeout=10)
        else:
            return {
                "ok": False,
                "endpoint": f"{method} {path}",
                "error": f"Unsupported method: {method}",
            }
    except Exception as exc:
        return {
            "ok": False,
            "endpoint": f"{method} {path}",
            "error": f"HTTP request failed: {exc}",
        }

    if response.status_code != 200:
        return {
            "ok": False,
            "endpoint": f"{method} {path}",
            "error": f"Expected 200, got {response.status_code}",
        }

    try:
        data = response.json()
    except Exception:
        return {
            "ok": False,
            "endpoint": f"{method} {path}",
            "error": "Response is not valid JSON",
        }

    schema_errors = validate_response_schema(data, response_schema)
    if schema_errors:
        return {
            "ok": False,
            "endpoint": f"{method} {path}",
            "error": " ; ".join(schema_errors),
        }

    return {
        "ok": True,
        "endpoint": f"{method} {path}",
        "error": None,
    }


def evaluate_system(spec: dict[str, Any], base_url: str) -> dict[str, Any]:
    endpoints = spec.get("api", {}).get("endpoints", [])
    if not isinstance(endpoints, list):
        fail("spec.api.endpoints missing or invalid")

    results: list[dict[str, Any]] = []
    missing_or_invalid: list[str] = []

    for endpoint in endpoints:
        result = evaluate_endpoint(base_url, endpoint)
        results.append(result)
        if not result["ok"]:
            missing_or_invalid.append(result["endpoint"])

    return {
        "goal_satisfied": len(missing_or_invalid) == 0,
        "base_url": base_url,
        "checked_endpoints": len(results),
        "failing_endpoints": missing_or_invalid,
        "results": results,
    }


def main() -> None:
    _, spec = read_spec()
    base_url = get_base_url()
    result = evaluate_system(spec, base_url)
    print(json.dumps(result, indent=2))

    if result["goal_satisfied"]:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
