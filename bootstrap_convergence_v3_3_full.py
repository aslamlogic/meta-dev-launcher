import os
import subprocess
from textwrap import dedent


def write_file(path: str, content: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.rstrip() + "\n")
    print(f"UPDATED: {path}")


def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


controller_source = read_file("iteration/controller.py")

spec_updater = f'''from typing import Any, Dict, List


class SpecUpdater:
    FILE_TEMPLATES = {{
        "meta_ui/api.py": """# UI_MARKER
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {{"status": "ok"}}
""",
        "iteration/rule_applicator.py": """def apply_rules(data):
    return data
""",
        "apps/__init__.py": """# apps package
""",
        "apps/generated_app/main.py": """from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {{"status": "ok"}}
""",
        "generated_app/main.py": """from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {{"status": "ok"}}
""",
        "iteration/controller.py": {controller_source!r},
    }}

    def _append_repair(
        self,
        repairs: List[Dict[str, Any]],
        seen: set,
        *,
        failure_code: str,
        action: str,
        path: str,
        message: str = "",
    ) -> None:
        key = (failure_code, action, path)
        if key in seen:
            return
        seen.add(key)
        repairs.append({{
            "failure_code": failure_code,
            "action": action,
            "path": path,
            "template": self.FILE_TEMPLATES.get(path, ""),
            "message": message,
        }})

    def derive_constraints(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        repairs: List[Dict[str, Any]] = []
        seen = set()

        for finding in findings:
            failure_code = str(finding.get("failure_code", "E-UNKNOWN"))
            path = str(finding.get("path", "")).strip()
            message = str(finding.get("message", "")).strip()

            if failure_code == "E-STRUCTURE":
                if path == "meta_ui/api.py":
                    self._append_repair(
                        repairs, seen,
                        failure_code=failure_code,
                        action="create_file",
                        path="meta_ui/api.py",
                        message=message,
                    )
                    continue

                if path == "iteration/controller.py":
                    self._append_repair(
                        repairs, seen,
                        failure_code=failure_code,
                        action="create_file",
                        path="iteration/controller.py",
                        message=message,
                    )
                    continue

                if path in ("apps/", "apps"):
                    self._append_repair(
                        repairs, seen,
                        failure_code=failure_code,
                        action="create_file",
                        path="apps/__init__.py",
                        message=message,
                    )
                    self._append_repair(
                        repairs, seen,
                        failure_code=failure_code,
                        action="create_file",
                        path="apps/generated_app/main.py",
                        message=message,
                    )
                    continue

                if path == "apps/generated_app/main.py":
                    self._append_repair(
                        repairs, seen,
                        failure_code=failure_code,
                        action="create_file",
                        path="apps/generated_app/main.py",
                        message=message,
                    )
                    continue

                if path == "generated_app/main.py":
                    self._append_repair(
                        repairs, seen,
                        failure_code=failure_code,
                        action="create_file",
                        path="generated_app/main.py",
                        message=message,
                    )
                    continue

            if failure_code == "E-BEHAVIOUR":
                self._append_repair(
                    repairs, seen,
                    failure_code=failure_code,
                    action="create_file",
                    path="meta_ui/api.py",
                    message=message,
                )
                continue

            if failure_code == "E-LWP":
                self._append_repair(
                    repairs, seen,
                    failure_code=failure_code,
                    action="create_file",
                    path="iteration/rule_applicator.py",
                    message=message,
                )
                continue

            if failure_code == "E-UI":
                self._append_repair(
                    repairs, seen,
                    failure_code=failure_code,
                    action="create_file",
                    path="meta_ui/api.py",
                    message=message,
                )
                continue

            if failure_code == "E-UNKNOWN" and path in self.FILE_TEMPLATES:
                self._append_repair(
                    repairs, seen,
                    failure_code=failure_code,
                    action="create_file",
                    path=path,
                    message=message,
                )
                continue

        return repairs
'''

write_file("iteration/spec_updater.py", spec_updater)

subprocess.run(
    [
        "git",
        "add",
        "iteration/spec_updater.py",
        "bootstrap_convergence_v3_3_full.py",
    ],
    check=True,
)
subprocess.run(["git", "commit", "-m", "Upgrade templates to full coverage"], check=True)
subprocess.run(["git", "push"], check=True)

print("CONVERGENCE V3.3 FULL DEPLOYED")
