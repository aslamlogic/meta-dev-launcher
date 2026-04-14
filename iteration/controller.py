import traceback
import importlib.util
import sys
from pathlib import Path

from iteration.generator import generate_app
from iteration.evaluator import evaluate_system


GENERATED_APP_PATH = Path("generated_app/main.py")


def load_generated_app():
    try:
        if not GENERATED_APP_PATH.exists():
            return None, f"LOAD_ERROR: {GENERATED_APP_PATH} missing"

        module_name = "generated_app.main"

        if module_name in sys.modules:
            del sys.modules[module_name]

        spec = importlib.util.spec_from_file_location(module_name, GENERATED_APP_PATH)
        if spec is None or spec.loader is None:
            return None, "LOAD_ERROR: could not create import spec"

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        if not hasattr(module, "app"):
            return None, "LOAD_ERROR: no app object"

        return module.app, None

    except Exception as e:
        return None, f"LOAD_ERROR: {str(e)}"


def update_spec(spec, evaluation):
    failing = evaluation.get("failing_endpoints", [])

    if not failing:
        return spec

    new_endpoints = []

    for ep in spec.get("endpoints", []):
        identifier = f"{ep.get('method')} {ep.get('path')}"
        if identifier not in failing:
            new_endpoints.append(ep)

    return {"endpoints": new_endpoints}


def run_iteration_loop(spec: dict):
    iterations = []
    max_iterations = 3

    try:
        for i in range(max_iterations):
            print(f"[ITERATION] Starting iteration {i+1}")

            generation_result = generate_app(spec)

            if generation_result.get("status") != "success":
                return {
                    "status": "failed",
                    "stage": "generation",
                    "error": generation_result
                }

            app, load_error = load_generated_app()

            if load_error:
                return {
                    "status": "failed",
                    "stage": "load",
                    "error": load_error
                }

            evaluation = evaluate_system(app, spec)

            status = "success" if evaluation.get("status") == "success" else "failed"

            iterations.append({
                "iteration": i + 1,
                "status": status,
                "evaluation": evaluation
            })

            print(f"[ITERATION] Completed iteration {i+1} with status: {status}")

            if status == "success":
                print(f"[ITERATION] Converged at iteration {i+1}")
                return {
                    "status": "converged",
                    "iterations": iterations
                }

            # update spec
            spec = update_spec(spec, evaluation)

        print("[ITERATION] Max iterations reached")

        return {
            "status": "failed",
            "reason": "max_iterations_reached",
            "iterations": iterations
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }
