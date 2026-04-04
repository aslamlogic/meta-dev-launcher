import traceback
from engine.llm_interface import generate_code
from engine.file_writer import write_app


def build_system(spec: dict):
    logs = []

    # STEP 1 — LLM call (this is where you are failing)
    try:
        code = generate_code(spec)
        logs.append("LLM call succeeded")
    except Exception as e:
        return {
            "status": "failure",
            "logs": [
                "LLM FAILURE",
                str(e),
                traceback.format_exc()
            ]
        }

    # STEP 2 — basic sanity
    if not code:
        return {
            "status": "failure",
            "logs": ["EMPTY CODE RETURNED FROM LLM"]
        }

    # STEP 3 — write (no validation yet)
    try:
        path = write_app(code)
        logs.append(f"Code written to {path}")
    except Exception as e:
        return {
            "status": "failure",
            "logs": [
                "FILE WRITE FAILURE",
                str(e),
                traceback.format_exc()
            ]
        }

    return {
        "status": "success",
        "logs": logs
    }
