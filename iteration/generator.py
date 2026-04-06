import os
from pathlib import Path


GENERATED_APP_DIR = Path("generated_app")
MAIN_FILE = GENERATED_APP_DIR / "main.py"


def generate_app(spec: dict) -> dict:
    try:
        GENERATED_APP_DIR.mkdir(parents=True, exist_ok=True)

        code = build_main_py(spec)

        with open(MAIN_FILE, "w") as f:
            f.write(code)

        return {
            "status": "success",
            "generated_files": [str(MAIN_FILE)]
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def build_main_py(spec: dict) -> str:
    return '''from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"status": "generated_app_running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/echo")
def echo(payload: dict):
    return {"received": payload}
'''
