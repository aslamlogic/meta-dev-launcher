import os
import shutil
import sys

TARGET_DIR = "generated_app"


def reset_directory():
    if os.path.exists(TARGET_DIR):
        shutil.rmtree(TARGET_DIR)
    os.makedirs(TARGET_DIR, exist_ok=True)


def write_app(code: str):
    reset_directory()

    # Ensure module cache is cleared BEFORE writing
    modules_to_delete = [m for m in sys.modules if m.startswith("generated_app")]
    for m in modules_to_delete:
        del sys.modules[m]

    if "/health" not in code:
        code = inject_health_endpoint(code)

    file_path = os.path.join(TARGET_DIR, "main.py")
    with open(file_path, "w") as f:
        f.write(code)

    init_path = os.path.join(TARGET_DIR, "__init__.py")
    with open(init_path, "w") as f:
        f.write("# generated package")

    return file_path


def inject_health_endpoint(code: str) -> str:
    health_code = """
@app.get("/health")
def health():
    return {"status": "ok"}
"""
    if "FastAPI(" in code:
        return code + health_code

    return f"""
from fastapi import FastAPI
app = FastAPI()
{health_code}
"""
