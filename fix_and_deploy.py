import subprocess
import sys
from pathlib import Path

def run(cmd):
    print(f"\n>> {cmd}")
    result = subprocess.run(cmd, shell=True, text=True)
    if result.returncode != 0:
        print(f"FAILED: {cmd}")
        sys.exit(1)

def write_render_yaml():
    content = """services:
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
    Path("render.yaml").write_text(content)
    print("render.yaml written")

def ensure_on_main():
    run("git fetch --all")
    run("git checkout main")

def recover_detached_commit():
    log = subprocess.check_output("git reflog -n 5", shell=True, text=True)
    for line in log.splitlines():
        if "Force runtime deps" in line:
            commit = line.split()[0]
            print(f"Found detached commit: {commit}")
            try:
                run(f"git cherry-pick {commit}")
            except SystemExit:
                print("Conflict detected, forcing resolution...")
                write_render_yaml()
                run("git add render.yaml")
                run("git cherry-pick --continue")
            return
    print("No detached commit found (ok)")

def force_clean_render_yaml():
    write_render_yaml()
    run("git add render.yaml")

def commit_and_push():
    run('git commit -m "AUTO FIX: enforce runtime + deps" || true')
    run("git push deploy-origin main --force-with-lease")

def main():
    print("=== AUTO FIX + DEPLOY ===")

    ensure_on_main()
    recover_detached_commit()
    force_clean_render_yaml()
    commit_and_push()

    print("\nDONE. Trigger deploy in Render.")

if __name__ == "__main__":
    main()
