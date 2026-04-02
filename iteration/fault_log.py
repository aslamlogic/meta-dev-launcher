import json
import os
from datetime import datetime


FAULT_LOG_PATH = "iteration/fault_log.jsonl"


def _ensure_log_file():
    directory = os.path.dirname(FAULT_LOG_PATH)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    if not os.path.exists(FAULT_LOG_PATH):
        with open(FAULT_LOG_PATH, "w") as f:
            pass


def _write_entry(entry: dict):
    with open(FAULT_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def log_faults(spec: dict, evaluation: dict) -> None:
    """
    Passive logging of failures.
    No effect on system behaviour.
    """

    _ensure_log_file()

    timestamp = datetime.utcnow().isoformat()

    # ---- NO ENDPOINT FAILURE ----
    if evaluation.get("reason") == "no endpoints defined":
        entry = {
            "timestamp": timestamp,
            "failure_type": "no_endpoints",
            "spec_snapshot": spec
        }
        _write_entry(entry)

    # ---- FAILING ENDPOINTS ----
    for ep in evaluation.get("failing_endpoints", []):
        entry = {
            "timestamp": timestamp,
            "failure_type": "endpoint_failure",
            "endpoint": ep,
            "spec_snapshot": spec
        }
        _write_entry(entry)

    # ---- SCHEMA MISMATCHES ----
    for mismatch in evaluation.get("schema_mismatches", []):
        entry = {
            "timestamp": timestamp,
            "failure_type": "schema_mismatch",
            "method": mismatch.get("method"),
            "path": mismatch.get("path"),
            "expected": mismatch.get("expected_response"),
            "actual": mismatch.get("actual_response"),
            "spec_snapshot": spec
        }
        _write_entry(entry)
