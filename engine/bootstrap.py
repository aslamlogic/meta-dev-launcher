import os
import sys
import json
import requests
import subprocess
from pathlib import Path

API_URL = "https://api.openai.com/v1/responses"

META_SPEC = "specs/meta.json"
ENGINE_SPEC = "specs/engine.json"
APP_SPEC = "specs/init.json"

FORBIDDEN = [".github/workflows/"]


def fail(msg):
    print(msg)
    sys.exit(1)


def read(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def detect_mode():
    if Path(META_SPEC).exists():
        return "meta", META_SPEC, read(META_SPEC)
    if Path(ENGINE_SPEC).exists():
        return "engine", ENGINE_SPEC, read(ENGINE_SPEC)
    if Path(APP_SPEC).exists():
        return "app", APP_SPEC, read(APP_SPEC)
    fail("No spec found")


def build_prompt(mode, spec):
    if mode == "meta":
        return f"""Generate META SYSTEM.

Return ONLY JSON:
{{"files":[{{"path":"...","content":"..."}}]}}

SYSTEM MUST:
- create orchestrator
- support multi-app builds
- support parallel execution
- include builder + deployer modules

OUTPUT DIR:
meta_system/

SPEC:
{json.dumps(spec)}
"""
    if mode == "engine":
        return f"""Upgrade engine. JSON only.
{{"files":[{{"path":"...","content":"..."}}]}}
SPEC:{json.dumps(spec)}"""
    return f"""Build app. JSON only.
{{"files":[{{"path":"...","content":"..."}}]}}
SPEC:{json.dumps(spec)}"""


def call(prompt):
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        fail("OPENAI_API_KEY not set")

    r = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-5.4-mini",
            "input": [{"role": "user", "content": prompt}]
        },
        timeout=120
    )

    if r.status_code != 200:
        fail(r.text)

    data = r.json()

    try:
        text = data["output"][0]["content"][0]["text"]
    except Exception:
        fail("Unexpected response format")

    print("===== OPENAI OUTPUT =====")
    print(text)
    print("===== END =====")

    try:
        return json.loads(text)
    except Exception as e:
        fail(f"JSON parse error: {e}")


def is_forbidden(path):
    return any(path.startswith(f) for f in FORBIDDEN)


def write(files):
    for f in files:
        path = f.get("path")
        content = f.get("content")

        if not path or not isinstance(content, str):
            fail("Invalid file entry")

        if is_forbidden(path):
            print("SKIP", path)
            continue

        safe_path = os.path.normpath(path)

        if safe_path.startswith("..") or os.path.isabs(safe_path):
            fail(f"Unsafe path: {path}")

        Path(safe_path).parent.mkdir(parents=True, exist_ok=True)

        with open(safe_path, "w", encoding="utf-8") as out:
            out.write(content)

        print("WROTE", safe_path)


def run_orchestrator():
    print("===== RUNNING META SYSTEM =====")

    try:
        subprocess.run(
            [sys.executable, "-m", "meta_system.orchestrator"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Orchestrator failed: {e}")

    print("===== META SYSTEM COMPLETE =====")


def main():
    mode, spec_path, spec = detect_mode()
    print("MODE:", mode)

    result = call(build_prompt(mode, spec))
    files = result.get("files")

    if not isinstance(files, list) or not files:
        fail("No files returned")

    write(files)

    # critical handoff
    if mode == "meta":
        run_orchestrator()


if __name__ == "__main__":
    main()
