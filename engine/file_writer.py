import os
import shutil


TARGET_DIR = "generated_app"


def reset_directory():
    if os.path.exists(TARGET_DIR):
        shutil.rmtree(TARGET_DIR)
    os.makedirs(TARGET_DIR, exist_ok=True)


def write_app(code: str):
    reset_directory()

    # Enforce /health endpoint
    if "/health" not in code:
        code = inject_health_endpoint(code)

    file_path = os.path.join(TARGET_DIR, "main.py")

    with open(file_path, "w") as f:
        f.write(code)

    return file_path


def inject_health_endpoint(code: str) -> str:
    health_code = """

@app.get("/health")
def health():
    return {"status": "ok"}
"""

    if "FastAPI(" in code:
        return code + health_code

    # fallback minimal app
    return f"""
from fastapi import FastAPI

app = FastAPI()

{health_code}
"""
