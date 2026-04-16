import os
import subprocess
from textwrap import dedent


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")
    print(f"UPDATED: {path}")


SPEC_UPDATER = dedent("""
from typing import Any, Dict, List


class SpecUpdater:

    FILE_TEMPLATES = {
        "meta_ui/api.py": '''# UI_MARKER
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
''',

        "iteration/rule_applicator.py": '''def apply_rules(data):
    return data
''',

        "apps/__init__.py": '''# apps package
''',

        "apps/generated_app/main.py": '''from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
''',

        "generated_app/main.py": '''from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
'''
    }

    def _add(self, repairs, seen, code, path, message):
        key = (code, path)
        if key in seen:
            return
        seen.add(key)

        repairs.append({
            "failure_code": code,
            "action": "create_file",
            "path": path,
            "template": self.FILE_TEMPLATES.get(path, ""),
            "message": message
        })

    def derive_constraints(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        repairs = []
        seen = set()

        for f in findings:
            code = str(f.get("failure_code", "E-UNKNOWN"))
            path = str(f.get("path", "")).strip()
            msg = str(f.get("message", ""))

            if code == "E-STRUCTURE":

                if path == "meta_ui/api.py":
                    self._add(repairs, seen, code, "meta_ui/api.py", msg)

                elif path in ("apps/", "apps"):
                    self._add(repairs, seen, code, "apps/__init__.py", msg)
                    self._add(repairs, seen, code, "apps/generated_app/main.py", msg)

                elif path == "generated_app/main.py":
                    self._add(repairs, seen, code, "generated_app/main.py", msg)

            elif code == "E-BEHAVIOUR":
                self._add(repairs, seen, code, "meta_ui/api.py", msg)

            elif code == "E-LWP":
                self._add(repairs, seen, code, "iteration/rule_applicator.py", msg)

            elif code == "E-UI":
                self._add(repairs, seen, code, "meta_ui/api.py", msg)

        return repairs
""")


write_file("iteration/spec_updater.py", SPEC_UPDATER)

subprocess.run(["git", "add", "."], check=True)
subprocess.run(["git", "commit", "-m", "Fix v3.3: remove controller self-generation"], check=True)
subprocess.run(["git", "push"], check=True)

print("CONVERGENCE V3.3 FIX APPLIED")
