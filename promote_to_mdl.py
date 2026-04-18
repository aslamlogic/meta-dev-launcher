import subprocess
import sys
import shutil
from pathlib import Path

ROOT = Path(".").resolve()
MDL_DIR = ROOT / "mdl-autonomous-build"

FILES_TO_PROMOTE = [
    "meta_ui/api.py",
    "iteration/controller.py",
    "requirements.txt",
    "runtime.txt",
    "render.yaml",
]

REQUIREMENTS = """fastapi==0.110.0
pydantic==1.10.13
uvicorn==0.27.1
"""

RUNTIME = "python-3.11.9\n"

RENDER = """services:
  - type: web
    name: mdl-autonomous-build
    env: python
    plan: starter
    buildCommand: |
      echo "fastapi==0.110.0" > requirements.txt
      echo "pydantic==1.10.13" >> requirements.txt
      echo "uvicorn==0.27.1" >> requirements.txt
      pip install -r requirements.txt
    startCommand: uvicorn meta_ui.api:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11.9
"""

def run(cmd):
    print(f">> {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        sys.exit(1)

def ensure_mdl_repo():
    if not MDL_DIR.exists():
        run("git clone https://ghu_encZjlgDZ3w0BWXDUx1tFNxwUtIUG3EwyT2@github.com/aslamlogic/mdl-autonomous-build.git")

def reset_mdl_repo():
    run(f"cd {MDL_DIR} && git fetch --all")
    run(f"cd {MDL_DIR} && git checkout main")
    run(f"cd {MDL_DIR} && git reset --hard origin/main")
    run(f"cd {MDL_DIR} && git clean -fd")

def copy_files():
    for file in FILES_TO_PROMOTE:
        src = ROOT / file
        dst = MDL_DIR / file
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"copied: {file}")

def enforce_files():
    (MDL_DIR / "requirements.txt").write_text(REQUIREMENTS)
    (MDL_DIR / "runtime.txt").write_text(RUNTIME)
    (MDL_DIR / "render.yaml").write_text(RENDER)
    print("enforced deterministic config")

def validate():
    run(f"cd {MDL_DIR} && python -m py_compile meta_ui/api.py iteration/controller.py")

def push():
    run(f"cd {MDL_DIR} && git add .")
    run(f'cd {MDL_DIR} && git commit -m "AUTO PROMOTE FROM META" || true')
    run(f"cd {MDL_DIR} && git push origin main --force-with-lease")

def main():
    ensure_mdl_repo()
    reset_mdl_repo()
    copy_files()
    enforce_files()
    validate()
    push()
    print("PROMOTION COMPLETE")

if __name__ == "__main__":
    main()
