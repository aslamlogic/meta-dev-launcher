import traceback
import importlib.util
import sys
from pathlib import Path

from iteration.generator import generate_app
from iteration.evaluator import evaluate_system


GENERATED_APP_PATH = Path("generated_app/main.py")


def load_generated_app():
    """
    Load generated_app/main.py and return FastAPI app object.
    """
    try:
        if not GENERATED_APP_PATH.exists():
            return None, f"LOAD_ERROR: {GENERATED_APP_PATH} missing"

        module_name = "generated_app.main"

        # Force fresh import each run
        if module_name in sys.modules:
            del sys.modules[module_name]

        spec = importlib.util.spec_from_file_location(module_name, GENERATED_APP_PATH)
        if spec is None or spec.loader is None:
            return None, "LOAD_ERROR: could not create import spec for generated_app.main"

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        if not hasattr(module, "app"):
            return None, "LOAD_ERROR: generated_app.main has no attribute 'app'"

        return module.app, None

    except Exception as e:
        return None, f"LOAD_ERROR: {str(e)}"


def run_iteration_loop(spec: dict):
    """
    Deterministic single-iteration controller.
    Flow:
    1. Generate app
    2. Load generated app
    3. Evaluate app against spec
    """
    iterations = []

    try:
        # STEP 1: generate app
        generation_result = generate_app(spec)

        if generation_result.get("status") != "success":
            return {
                "status": "failed",
                "stage": "generation",
                "error": generation_result
            }

        # STEP 2: load generated app
        app, load_error = load_generated_app()

        if load_error:
            iterations.append({
                "iteration": 1,
                "status": "failed",
                "evaluation": {
                    "status": "failure",
                    "logs": [load_error],
                    "failing_endpoints": [],
                    "schema_mismatches": []
                }
            })
            return {
                "status": "started",
                "iterations": iterations
            }

        # STEP 3: evaluate app  ← FIXED CALL
        evaluation = evaluate_system(app, spec)

        iterations.append({
            "iteration": 1,
            "status": "success" if evaluation.get("status") == "success" else "failed",
            "evaluation": evaluation
        })

        return {
            "status": "started",
            "iterations": iterations
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }
