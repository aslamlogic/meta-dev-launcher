import os
from engine.llm_interface import generate
from iteration.spec_updater import SpecUpdater
from iteration.evaluator import evaluate

class IterationController:

    def __init__(self, max_iterations=5):
        self.max_iterations = max_iterations
        self.spec_updater = SpecUpdater()

    def run(self, workspace_path, initial_spec_text, run_id="run"):

        spec = initial_spec_text
        last_score = -9999

        for i in range(self.max_iterations):
            print(f"ITERATION {i}")

            allowed_files = ["generated_app/main.py"]

            output = generate(spec, [], allowed_files)

            output_path = os.path.join(workspace_path, "generated_app/main.py")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, "w") as f:
                f.write(output)

            result = evaluate(output)

            findings = result.get("findings", [])
            passed = result.get("passed", False)

            score = len(findings) * -1

            print(f"Score: {score}")

            if passed:
                print("VALIDATED_BUILD")
                return {"status": "SUCCESS"}

            if score <= last_score:
                print("NO IMPROVEMENT → STOP")
                return {"status": "FAIL"}

            last_score = score

            constraints = self.spec_updater.derive_constraints(findings)

            spec += "\n\nFIX:\n" + str(constraints)

        return {"status": "FAIL"}
