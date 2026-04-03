import json
import uuid
from pathlib import Path

from iteration.build import build_system
from iteration.runtime import start_server
from iteration.evaluator import evaluate_system
from iteration.spec_updater import update_spec


ROOT = Path(__file__).resolve().parent.parent
SPECS_DIR = ROOT / "specs"
SPECS_DIR.mkdir(parents=True, exist_ok=True)


def run_iteration_loop(spec: dict, max_iterations: int = 3):
    print("=== CONTROLLER STARTED ===", flush=True)

    build_id = f"build_{uuid.uuid4().hex[:8]}"
    working_spec = spec
    all_logs: list[str] = []

    for iteration in range(1, max_iterations + 1):
        print(f"=== ITERATION {iteration} START ===", flush=True)
        all_logs.append(f"=== ITERATION {iteration} START ===")

        spec_path = SPECS_DIR / "init.json"
        spec_path.write_text(json.dumps(working_spec, indent=2), encoding="utf-8")
        print(f"SPEC WRITTEN: {spec_path}", flush=True)
        all_logs.append(f"SPEC WRITTEN: {spec_path}")

        build = build_system(working_spec)
        print(f"=== BUILD RESULT === {build}", flush=True)
        all_logs.extend(build.get("logs", []))

        runtime = start_server()
        print(f"=== RUNTIME RESULT === {runtime}", flush=True)
        all_logs.extend(runtime.get("logs", []))

        evaluation = evaluate_system(working_spec)
        print(f"=== EVALUATION RESULT === {evaluation}", flush=True)
        all_logs.append(f"EVALUATION: {evaluation}")

        if evaluation.get("status") == "success":
            print(f"=== ITERATION {iteration} SUCCESS ===", flush=True)
            all_logs.append(f"=== ITERATION {iteration} SUCCESS ===")
            result = {
                "build_id": build_id,
                "message": "Build converged successfully",
                "deployment_url": evaluation.get("base_url", "http://localhost:8000"),
                "logs": all_logs,
                "evaluation": evaluation,
                "success": True,
                "iterations_used": iteration,
                "normalized_spec": working_spec,
            }
            print(f"=== FINAL RESULT === {result}", flush=True)
            return result

        print(f"=== ITERATION {iteration} FAILED - UPDATING SPEC ===", flush=True)
        all_logs.append(f"=== ITERATION {iteration} FAILED - UPDATING SPEC ===")

        updated_spec = update_spec(working_spec, evaluation)
        if updated_spec == working_spec:
            print("=== SPEC UPDATER MADE NO CHANGES ===", flush=True)
            all_logs.append("=== SPEC UPDATER MADE NO CHANGES ===")
            result = {
                "build_id": build_id,
                "message": "Build failed and no corrective update was available",
                "deployment_url": evaluation.get("base_url", "http://localhost:8000"),
                "logs": all_logs,
                "evaluation": evaluation,
                "success": False,
                "iterations_used": iteration,
                "normalized_spec": working_spec,
            }
            print(f"=== FINAL RESULT === {result}", flush=True)
            return result

        working_spec = updated_spec
        print(f"=== UPDATED SPEC === {working_spec}", flush=True)
        all_logs.append(f"UPDATED SPEC: {working_spec}")

    result = {
        "build_id": build_id,
        "message": "Build stopped at max iteration limit without convergence",
        "deployment_url": "http://localhost:8000",
        "logs": all_logs,
        "evaluation": evaluation,
        "success": False,
        "iterations_used": max_iterations,
        "normalized_spec": working_spec,
    }
    print(f"=== FINAL RESULT === {result}", flush=True)
    return result


run_iteration_loop({})
