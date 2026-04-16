import os
import subprocess
from textwrap import dedent


def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"UPDATED: {path}")


# =========================
# SPEC UPDATER (v3.1)
# =========================
SPEC_UPDATER = dedent("""
from typing import Any, Dict, List


class SpecUpdater:

    FILE_TEMPLATES = {
        "meta_ui/api.py": '''from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
''',

        "iteration/rule_applicator.py": '''def apply_rules(data):
    return data
''',

        "apps/__init__.py": '''# apps package'''
    }

    def derive_constraints(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        repair_contract = []

        for finding in findings:
            failure_code = finding.get("failure_code", "E-UNKNOWN")
            path = finding.get("path", "")

            action = "fix"

            if failure_code == "E-STRUCTURE":
                if path in self.FILE_TEMPLATES:
                    action = "create_file"

            if failure_code == "E-LWP":
                path = "iteration/rule_applicator.py"
                action = "create_file"

            if failure_code == "E-UI":
                path = "meta_ui/api.py"
                action = "create_file"

            repair_contract.append({
                "failure_code": failure_code,
                "action": action,
                "path": path,
                "template": self.FILE_TEMPLATES.get(path, ""),
                "message": finding.get("message", "")
            })

        return repair_contract
""")


# =========================
# CONTROLLER (v3.2)
# =========================
CONTROLLER = dedent("""
import os
from typing import Any, Dict, List, Set

from engine.llm_interface import generate
from iteration.evaluator import evaluate
from iteration.spec_updater import SpecUpdater


class IterationController:
    def __init__(self, max_iterations: int = 5):
        self.max_iterations = max_iterations
        self.spec_updater = SpecUpdater()

    def _allowed_files(self) -> List[str]:
        return [
            "generated_app/main.py",
            "apps/generated_app/main.py",
            "meta_ui/api.py",
            "iteration/rule_applicator.py",
            "apps/__init__.py",
        ]

    def _write_single(self, workspace_path, path, content):
        full = os.path.join(workspace_path, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)

    def _apply_templates(self, workspace_path, repairs):
        for r in repairs:
            if r.get("action") == "create_file":
                path = r.get("path")
                template = r.get("template", "")
                if path and template:
                    self._write_single(workspace_path, path, template)
                    print(f"TEMPLATE CREATED: {path}")

    def _collect_main(self, workspace_path):
        for p in ["generated_app/main.py", "apps/generated_app/main.py"]:
            full = os.path.join(workspace_path, p)
            if os.path.exists(full):
                return open(full).read()
        return ""

    def _score(self, result):
        return (10 if result.get("passed") else 0) - len(result.get("findings", []))

    def _sig(self, result):
        return set(f"{f.get('failure_code')}|{f.get('path')}" for f in result.get("findings", []))

    def run(self, workspace_path, initial_spec_text, run_id="run"):
        prev_score = None
        prev_sig = set()
        repairs = []

        for i in range(self.max_iterations):
            print(f"ITERATION {i}")

            self._apply_templates(workspace_path, repairs)

            files = generate(initial_spec_text, repairs, self._allowed_files())
            for path, content in files.items():
                self._write_single(workspace_path, path, content)

            result = evaluate(self._collect_main(workspace_path))
            score = self._score(result)
            print(f"Score: {score}")

            if result.get("passed"):
                print("VALIDATED_BUILD")
                return {"status": "SUCCESS", "score": score}

            sig = self._sig(result)

            if prev_score is not None and score <= prev_score:
                print("NO IMPROVEMENT -> STOP")
                return {"status": "FAIL", "reason": "no_improvement"}

            if sig == prev_sig:
                print("IDENTICAL FAILURE SIGNATURE -> STOP")
                return {"status": "FAIL", "reason": "stuck"}

            repairs = self.spec_updater.derive_constraints(result.get("findings", []))
            prev_score = score
            prev_sig = sig

        return {"status": "FAIL", "reason": "max_iterations"}
""")


# =========================
# WRITE FILES
# =========================
write_file("iteration/spec_updater.py", SPEC_UPDATER)
write_file("iteration/controller.py", CONTROLLER)

# =========================
# COMMIT + PUSH
# =========================
subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "Convergence v3.2 FULL"], check=True)
subprocess.run(["git", "push"], check=True)

print("CONVERGENCE V3.2 FULL DEPLOYED")
