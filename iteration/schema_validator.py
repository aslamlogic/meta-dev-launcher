from typing import Any, Dict, List


def _type_name(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int) and not isinstance(value, bool):
        return "number"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def validate_json_schema(expected: Dict[str, Any], actual: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Minimal deterministic schema validator.

    Expected schema format example:
    {
        "status": "string",
        "count": "number"
    }

    Returns a list of mismatches.
    Empty list means schema valid.
    """

    mismatches: List[Dict[str, Any]] = []

    for key, expected_type in expected.items():
        if key not in actual:
            mismatches.append(
                {
                    "field": key,
                    "issue": "missing_field",
                    "expected": expected_type,
                    "actual": None,
                }
            )
            continue

        actual_value = actual[key]
        actual_type = _type_name(actual_value)

        if expected_type != actual_type:
            mismatches.append(
                {
                    "field": key,
                    "issue": "type_mismatch",
                    "expected": expected_type,
                    "actual": actual_type,
                }
            )

    return mismatches
