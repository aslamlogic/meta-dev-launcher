import os
import sys
import json
import requests
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
    return json.load(open(path, "r"))


def detect_mode():
    if Path(META_SPEC).exists():
        return "meta", META_SPEC, read(META_SPEC)
    if Path(ENGINE_SPEC).exists():
        return "engine", ENGINE_SPEC, read(ENGINE_SPEC)
    if Path(APP_SPEC).exists():
        return "app", APP_SPEC, read(APP_SPEC)
    fail("No spec found")


def prompt(mode, spec):
    if mode == "meta":
        return f"""Generate a META SYSTEM.

Return ONLY JSON:
{{
  "files": [{{"path":"...","content":"..."}}]
}}

SYSTEM MUST:
- create orchestrator
- support multiple app builds
- support parallel execution
- call builders and deployers
- be runnable

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
        fail("No API key")

    r = requests.post(
        API_URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={
            "model": "gpt-5.4-mini",
            "input": [{"role": "user", "content": prompt}]
        }
    )

    if r.status_code != 200:
        fail(r.text)

    text = r.json()["output"][0]["content"][0]["text"]
    print(text)
    return json.loads(text)


def safe(path):
    if any(path.startswith(f) for f in FORBIDDEN):
        print("SKIP", path)
        return None
    return path


def write(files):
    for f in files:
        p = safe(f["path"])
        if not p:
            continue
        Path(p).parent.mkdir(parents=True, exist_ok=True)
        open(p, "w").write(f["content"])
        print("WROTE", p)


def main():
    mode, path, spec = detect_mode()
    print("MODE:", mode)

    out = call(prompt(mode, spec))
    write(out["files"])


if __name__ == "__main__":
    main()
