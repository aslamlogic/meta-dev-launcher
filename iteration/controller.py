from iteration.evaluator import evaluate_app
from iteration.generator import generate_code
from iteration.spec_updater import update_spec_with_failures
from iteration.prompt_builder import build_prompt


MAX_ITERATIONS = 3


def run_iteration_loop(spec: dict, smr: str):
    """
    Deterministic iteration loop.

    Inputs:
        spec (dict)
        smr (str)

    Output:
        structured iteration results
    """

    iterations = []

    for i in range(1, MAX_ITERATIONS + 1):
        try:
            # ---------- BUILD PROMPT ----------
            prompt = build_prompt(spec, smr)

            # ---------- GENERATE APP ----------
            app = generate_code(prompt)

            # ---------- EVALUATE ----------
            evaluation = evaluate_app(app, spec)

            status = "passed" if evaluation["status"] == "success" else "failed"

            iterations.append({
                "iteration": i,
                "status": status,
                "evaluation": evaluation
            })

            # ---------- SUCCESS EXIT ----------
            if evaluation["status"] == "success":
                return {
                    "status": "success",
                    "iterations": iterations
                }

            # ---------- UPDATE SPEC ----------
            spec = update_spec_with_failures(spec, evaluation)

        except Exception as e:
            iterations.append({
                "iteration": i,
                "status": "error",
                "error": str(e)
            })

            return {
                "status": "error",
                "iterations": iterations
            }

    # ---------- MAX ITERATIONS ----------
    return {
        "status": "failed",
        "reason": "max_iterations_reached",
        "iterations": iterations
    }
