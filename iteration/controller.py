import traceback
from iteration.generator import generate_app
from iteration.evaluator import evaluate_system
from importlib import import_module


def load_generated_app():
    try:
        module = import_module("generated_app.main")
        return module.app
    except Exception as e:
        return None, f"LOAD_ERROR: {str(e)}"


def run_iteration_loop(spec: dict):
    iterations = []

    try:
        # STEP 1 — Generate app
        generate_app(spec)

        # STEP 2 — Load generated app
        loaded = load_generated_app()

        if isinstance(loaded, tuple):
            app, load_error = None, loaded[1]
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

        app = loaded

        # STEP 3 — Evaluate (FIX IS HERE)
        evaluation = evaluate_system(app, spec)

        iterations.append({
            "iteration": 1,
            "status": "success" if evaluation["status"] == "success" else "failed",
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
