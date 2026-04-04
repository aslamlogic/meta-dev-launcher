import traceback
from engine.llm_interface import generate_code
from engine.file_writer import write_app


def build_system(spec: dict):
    logs = []

    try:
        logs.append("Starting build")

        code = generate_code(spec)
        logs.append("Code generated")

        path = write_app(code)
        logs.append(f"Code written to {path}")

        return {
            "status": "success",
            "logs": logs
        }

    except Exception as e:
        error_trace = traceback.format_exc()

        logs.append(f"BUILD FAILED: {str(e)}")
        logs.append(error_trace)

        return {
            "status": "failure",
            "logs": logs
        }
