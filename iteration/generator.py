import os
from pathlib import Path


GENERATED_APP_DIR = Path("generated_app")
MAIN_FILE = GENERATED_APP_DIR / "main.py"


def generate_app(spec: dict) -> dict:
    try:
        print("[GENERATOR] Starting generation")

        GENERATED_APP_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[GENERATOR] Ensured directory exists: {GENERATED_APP_DIR}")

        code = build_main_py(spec)
        print("[GENERATOR] Code built")

        with open(MAIN_FILE, "w") as f:
            f.write(code)

        print(f"[GENERATOR] Wrote file: {MAIN_FILE.resolve()}")

        return {
            "status": "success",
            "generated_files": [str(MAIN_FILE.resolve())]
        }

    except Exception as e:
        print(f"[GENERATOR] ERROR: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }


def build_main_py(spec: dict) -> str:
    endpoints = spec.get("endpoints", [])

    routes = []

    for ep in endpoints:
        method = ep.get("method", "GET").lower()
        path = ep.get("path", "/")

        func_name = path.strip("/").replace("/", "_") or "root"

        if method == "get":
            routes.append(f"""
@app.get("{path}")
def {func_name}():
    return {{"endpoint": "{path}", "status": "ok"}}
""")

        elif method == "post":
            routes.append(f"""
@app.post("{path}")
def {func_name}(payload: dict):
    return {{"endpoint": "{path}", "received": payload}}
""")

    routes_code = "\n".join(routes)

    return f'''
from fastapi import FastAPI

app = FastAPI()

{routes_code}
'''
