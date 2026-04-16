import os
import subprocess
from textwrap import dedent


def write_file(path: str, content: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"UPDATED: {path}")


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


write_file("iteration/spec_updater.py", SPEC_UPDATER)


subprocess.run(["git", "add", "iteration/spec_updater.py"], check=True)
subprocess.run(["git", "commit", "-m", "Convergence v3.1: template-driven repair"], check=True)
subprocess.run(["git", "push"], check=True)

print("CONVERGENCE V3.1 DEPLOYED")
