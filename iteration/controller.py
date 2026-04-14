from iteration.generator import generate_app
from iteration.evaluator import evaluate_app


def run_iteration_loop(spec, max_iterations=3):
    print("🔥 NEW CONTROLLER ACTIVE 🔥")

    iterations = []

    for i in range(1, max_iterations + 1):
        print(f"[ITERATION] Starting iteration {i}")

        # Generate code
        generate_app(spec)

        # Evaluate generated app
        evaluation = evaluate_app(spec)

        status = "success" if evaluation["status"] == "success" else "failed"

        iterations.append({
            "iteration": i,
            "status": status,
            "evaluation": evaluation
        })

        print(f"[ITERATION] Completed iteration {i} with status: {status}")

        if status == "success":
            print(f"[ITERATION] Converged at iteration {i}")
            return {
                "status": "converged",
                "iterations": iterations
            }

    print("[ITERATION] Max iterations reached")

    return {
        "status": "failed",
        "reason": "max_iterations_reached",
        "iterations": iterations
    }
