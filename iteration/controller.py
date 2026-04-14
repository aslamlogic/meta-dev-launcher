import traceback
from iteration.evaluator import evaluate_app
from iteration.spec_updater import update_spec_with_failures
from iteration.generator import generate_code
from iteration.prompt_builder import build_prompt


MAX_ITERATIONS = 3


def run_iteration_loop(spec: dict, smr: str):
    """
    Main deterministic iteration loop.
    """

    iterations = []

    try:

        for i in range(1, MAX_ITERATIONS + 1):

            # --------------------------------------------------
            # BUILD PROMPT (CRITICAL FIX — constraint injection)
            # --------------------------------------------------
            prompt = build_prompt(spec, smr)

            # --------------------------------------------------
            # GENERATE CODE
            # --------------------------------------------------
            try:
                app = generate_code(prompt)
            except Exception as e:
                iterations.append({
                    "iteration": i,
                    "status": "failed",
                    "evaluation": {
                        "status": "failure",
                        "logs": [f"GENERATION ERROR → {str(e)}"],
                        "failing_endpoints": [],
                        "schema_mismatches": []
                    }
                })
                break

            # --------------------------------------------------
            # EVALUATE
            # --------------------------------------------------
            evaluation = evaluate_app(app, spec)

            # --------------------------------------------------
            # STORE ITERATION RESULT
            # --------------------------------------------------
            iteration_result = {
                "iteration": i,
                "status": "passed" if evaluation["status"] == "success" else "failed",
                "evaluation": evaluation
            }

            iterations.append(iteration_result)

            # --------------------------------------------------
            # SUCCESS EXIT
            # --------------------------------------------------
            if evaluation["status"] == "success":
                return {
                    "status": "success",
                    "iterations": iterations
                }

            # --------------------------------------------------
            # UPDATE SPEC WITH FAILURES (CRITICAL)
            # --------------------------------------------------
            spec = update_spec_with_failures(spec, evaluation)

        # ------------------------------------------------------
        # MAX ITERATIONS REACHED
        # ------------------------------------------------------
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
