import os
from pathlib import Path

BASE = Path(".")


def write_file(path, content, overwrite=False):
    p = BASE / path
    p.parent.mkdir(parents=True, exist_ok=True)

    if p.exists() and not overwrite:
        new_path = p.with_suffix(p.suffix + ".new")
        with open(new_path, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        print(f"[SAFE] Existing file preserved → {new_path}")
    else:
        with open(p, "w", encoding="utf-8") as f:
            f.write(content.strip() + "\n")
        print(f"[WRITE] {path}")


def main():
    print("=== META FULL SYSTEM INSTALL ===")

    # ---- ROOT ----

    write_file("Procfile", "web: uvicorn meta_ui.api:app --host 0.0.0.0 --port $PORT", overwrite=True)

    write_file("requirements.txt", """
fastapi
uvicorn
httpx
pytest
openai
""", overwrite=True)

    write_file(".github/workflows/meta.yml", """
name: Meta Build System

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: python iteration/controller.py
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
""", overwrite=True)

    # ---- ENGINE ----

    write_file("engine/output_cleaner.py", """
def clean_output(text: str) -> str:
    return text.replace("```python", "").replace("```", "").strip()
""")

    # ---- ITERATION ADDITIONS ----

    write_file("iteration/git_service.py", """
def commit():
    print("git commit placeholder")
""")

    write_file("iteration/deploy.py", """
def deploy():
    print("railway deploy handled externally")
""")

    write_file("iteration/runtime_probe.py", """
def probe():
    return True
""")

    write_file("iteration/logging_service.py", """
def log_event(msg):
    print(msg)
""")

    write_file("iteration/fault_logger.py", """
def log_fault(msg):
    print("FAULT:", msg)
""")

    write_file("iteration/report_builder.py", """
def build_report():
    return {}
""")

    write_file("iteration/convergence.py", """
def converged(result):
    return result.get("status") == "pass"
""")

    write_file("iteration/budget_service.py", """
def allow():
    return True
""")

    write_file("iteration/environment_validator.py", """
import os

def validate_env():
    if not os.getenv("OPENAI_API_KEY"):
        raise Exception("Missing OPENAI_API_KEY")
""")

    write_file("iteration/governance_filter.py", """
def enforce(text: str):
    return "```" not in text
""")

    write_file("iteration/security_evaluator.py", """
def check(text: str):
    return "subprocess" not in text
""")

    write_file("iteration/failure_classifier.py", """
def classify(error):
    return "FAILURE"
""")

    write_file("iteration/smr_registry.py", """
SMR = {"rules": ["code_only", "no_markdown"]}
""")

    write_file("iteration/smr_service.py", """
from iteration.smr_registry import SMR

def get_active_smr():
    return SMR
""")

    # ---- META UI ----

    write_file("meta_ui/api.py", """
from fastapi import FastAPI
from iteration.controller import main

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/runs")
def run():
    main()
    return {"status": "started"}
""", overwrite=True)

    # ---- TESTS ----

    write_file("tests/test_basic.py", """
def test_ok():
    assert True
""")

    # ---- SMR ----

    write_file("smr/registry.json", """
{
  "active": "default"
}
""")

    write_file("smr/rules/smr_v_current.txt", """
code_only
no_markdown
""")

    print("=== INSTALL COMPLETE ===")


if __name__ == "__main__":
    main()
