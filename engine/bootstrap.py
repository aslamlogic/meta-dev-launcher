import os
import json
import requests
import re
import subprocess
import time


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


def _generate_code(spec: dict) -> dict:
    prompt = f"""
You must return ONLY valid JSON. No explanations. No markdown.

Schema:
{{
  "files": {{
    "main.py": "string"
  }}
}}

Generate a FastAPI application with a /health endpoint returning {{ "status": "ok" }}.

Spec:
{json.dumps(spec, indent=2)}
"""

    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": OPENAI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0
        },
    )

    data = response.json()

    if "choices" not in data:
        raise RuntimeError(f"OpenAI API error: {data}")

    content = data["choices"][0]["message"]["content"].strip()

    try:
        parsed = json.loads(content)
        return parsed.get("files", {})
    except Exception:
        pass

    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            return parsed.get("files", {})
        except Exception:
            pass

    raise RuntimeError(f"Invalid JSON from model:\n{content}")


def _write_files(files: dict) -> None:
    for path, content in files.items():
        with open(path, "w") as f:
            f.write(content)


def _start_server():
    print("STARTING SERVER...")

    process = subprocess.Popen(
        ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(3)  # allow server to start

    return process


def build_system(spec: dict) -> None:
    print("BUILDING SYSTEM...")

    files = _generate_code(spec)

    _write_files(files)

    print("BUILD COMPLETE")

    _start_server()
