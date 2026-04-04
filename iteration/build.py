import traceback
from engine.llm_interface import generate_code
from engine.file_writer import write_app


def build_system(spec: dict):
    logs = []

    try:
        code = generate_code(spec)
        logs.append("Code generated")

        # HARD VALIDATION
        if "FastAPI" not in code:
            raise ValueError("Missing FastAPI import")

        if "app = FastAPI()" not in code:
            raise ValueError("Missing FastAPI app instance")

        if "@" not in code:
            raise ValueError("No endpoints defined")

        # Try compiling code BEFORE writing
        try:
            compile(code, "<generated_app>", "exec")
        except Exception as e:
            raise ValueError(f"Syntax error: {e}")

        path = write_app(code)
        logs.append(f"Code written to {path}")

        return {"status": "success", "logs": logs}

    except Exception as e:
        logs.append(f"BUILD FAILURE: {str(e)}")
        logs.append(traceback.format_exc())

        return {
            "status": "failure",
            "logs": logs,
        }
