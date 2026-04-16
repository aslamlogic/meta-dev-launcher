import os
import subprocess

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"UPDATED: {path}")

# =========================
# engine/llm_interface.py
# =========================
llm_interface = '''import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate(spec_text, constraints, allowed_files):
    system_message = """
You are a deterministic code repair engine.

RULES:
- ONLY fix the listed failures
- ONLY modify allowed files
- DO NOT introduce new files
- DO NOT modify unrelated logic
- Output ONLY valid Python code
"""

    constraint_text = "\\n".join([
        f"{c['failure_code']} → {c['constraint']}" for c in constraints
    ])

    user_message = f"""
SPEC:
{spec_text}

CONSTRAINTS:
{constraint_text}

ALLOWED FILES:
{allowed_files}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    )

    return response.choices[0].message.content
'''

# =========================
# iteration/spec_updater.py
# =========================
spec_updater = '''class SpecUpdater:

    def derive_constraints(self, findings):
        constraints = []

        for f in findings:
            constraints.append({
                "failure_code": f.get("failure_code"),
                "constraint": f.get("message"),
                "path": f.get("path")
            })

        return constraints
'''

# =========================
# iteration/controller.py
# =========================
controller = '''import os
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

            spec += "\\n\\nFIX:\\n" + str(constraints)

        return {"status": "FAIL"}
'''

# WRITE FILES
write_file("engine/llm_interface.py", llm_interface)
write_file("iteration/spec_updater.py", spec_updater)
write_file("iteration/controller.py", controller)

# GIT OPERATIONS
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", "Convergence hardening applied"])
subprocess.run(["git", "push"])

print("CONVERGENCE HARDENING DEPLOYED")
