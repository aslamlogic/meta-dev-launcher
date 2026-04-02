import json
import os
import re
import subprocess
import sys
from pathlib import Path

import requests

CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"

SPEC_CANDIDATES = [
    Path("specs/init.json"),
    Path("specs/app.json"),
]

FORBIDDEN_PREFIXES = (
    ".git/",
    ".github/workflows/",
)

OUTPUT_SCHEMA = {
    "name": "generated_files",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "files": {
                "type": "array",
                "minItems": 2,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                    },
                    "required": ["path", "content"],
                },
            }
        },
        "required": ["files"],
    },
}


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    sys.exit(1)


def read_spec() -> tuple[Path, dict]:
    for path in SPEC_CANDIDATES:
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                return path, json.load(f)
    fail("No spec found. Expected specs/init.json or specs/app.json.")


def build_messages(spec_path: Path, spec: dict) -> list[dict]:
    return [
        {
            "role": "system",
            "content": (
                "You are a deterministic software generator.\n"
                "Return ONLY valid JSON matching the schema.\n"
                "No markdown. No commentary. No prose.\n"
                "Generate full files only.\n"
                "Allowed outputs: main.py and requirements.txt only.\n"
                "Use FastAPI and Pydantic.\n"
                "STRICT RULES:\n"
                "- You MUST implement ALL endpoints defined in api.endpoints\n"
                "- For EACH endpoint:\n"
                "  • Use EXACT decorator format: @app.<method>(\"<path>\")\n"
                "  • Method must match exactly (get, post, etc.)\n"
                "  • Path must match exactly\n"
                "- If ANY endpoint is missing, output is INVALID\n"
                "- DO NOT omit endpoints\n"
            ),
        },
        {
            "role": "user",
            "content": (
                f"Specification source: {spec_path.as_posix()}\n\n"
                f"Specification:\n{json.dumps(spec, indent=2, ensure_ascii=False)}\n\n"
                "Requirements:\n"
                "1. Generate a complete runnable FastAPI application.\n"
                "2. Main application file must be main.py.\n"
                "3. requirements.txt must include all necessary packages.\n"
                "4. Implement endpoints EXACTLY as defined.\n"
                "5. GET endpoints return valid JSON.\n"
                "6. POST endpoints must use Pydantic BaseModel.\n"
                "7. No extra files.\n"
            ),
        },
    ]


def call_openai(messages: list[dict]) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        fail("OPENAI_API_KEY not set")

    response = requests.post(
        CHAT_COMPLETIONS_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": messages,
            "response_format": {
                "type": "json_schema",
                "json_schema": OUTPUT_SCHEMA,
            },
            "temperature": 0,
        },
        timeout=180,
    )

    if response.status_code != 200:
        fail(f"OpenAI error: {response.status_code} {response.text}")

    try:
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception as exc:
        fail(f"Invalid JSON from model: {exc}")


def normalise_content(content: str) -> str:
    content = content.strip()

    fenced = re.fullmatch(r"```[a-zA-Z0-9_-]*\n(.*)\n```", content, re.DOTALL)
    if fenced:
        content = fenced.group(1)

    if "```" in content:
        fail("Markdown fence detected in generated content")

    return content


def validate_path(path_str: str) -> Path:
    if not path_str or not isinstance(path_str, str):
        fail("Validation failed: invalid file path")

    if any(path_str.startswith(prefix) for prefix in FORBIDDEN_PREFIXES):
        fail(f"Validation failed: forbidden path {path_str}")

    path = Path(path_str)

    if path.is_absolute():
        fail(f"Validation failed: absolute path not allowed {path_str}")

    if ".." in path.parts:
        fail(f"Validation failed: path traversal detected {path_str}")

    return path


def validate_files(payload: dict, spec: dict) -> None:
    files = payload.get("files")
    if not isinstance(files, list) or not files:
        fail("Validation failed: no files returned")

    by_path: dict[str, str] = {}

    for item in files:
        if not isinstance(item, dict):
            fail("Validation failed: file item must be an object")

        path = item.get("path")
        content = item.get("content")

        if not isinstance(path, str):
            fail("Validation failed: file path missing")
        if not isinstance(content, str) or not content.strip():
            fail(f"Validation failed: empty content in {path}")

        validate_path(path)
        by_path[path] = normalise_content(content)

    if "main.py" not in by_path:
        fail("Validation failed: main.py missing")
    if "requirements.txt" not in by_path:
        fail("Validation failed: requirements.txt missing")
    if len(by_path) != 2:
        fail(f"Validation failed: unexpected files returned {list(by_path.keys())}")

    main_py = by_path["main.py"]
    requirements_txt = by_path["requirements.txt"].lower()

    if "FastAPI" not in main_py:
        fail("Validation failed: FastAPI missing in main.py")
    if "app = FastAPI()" not in main_py:
        fail("Validation failed: app instance missing in main.py")
    if "fastapi" not in requirements_txt:
        fail("Validation failed: fastapi missing in requirements.txt")
    if "uvicorn" not in requirements_txt:
        fail("Validation failed: uvicorn missing in requirements.txt")

    endpoints = spec.get("api", {}).get("endpoints", [])
    if not isinstance(endpoints, list):
        fail("Validation failed: spec.api.endpoints missing or invalid")

    for endpoint in endpoints:
        method = str(endpoint.get("method", "")).lower()
        path = endpoint.get("path")

        if not method or not path:
            fail("Validation failed: endpoint missing method or path in spec")

        decorator = f'@app.{method}("{path}")'
        if decorator not in main_py:
            fail(f"Validation failed: endpoint decorator missing {decorator}")

        if method == "post" and "BaseModel" not in main_py:
            fail("Validation failed: BaseModel missing for POST endpoint support")


def write_files(payload: dict) -> None:
    for item in payload["files"]:
        path = validate_path(item["path"])
        content = normalise_content(item["content"])

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content + ("\n" if not content.endswith("\n") else ""), encoding="utf-8")
        print(f"WROTE {path.as_posix()}")


def git_commit_generated_files() -> None:
    add = subprocess.run(
        ["git", "add", "main.py", "requirements.txt"],
        capture_output=True,
        text=True,
    )
    if add.returncode != 0:
        fail(f"git add failed: {add.stderr}")

    diff = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        capture_output=True,
        text=True,
    )

    if diff.returncode == 0:
        print("NO CHANGES TO COMMIT")
        return

    commit = subprocess.run(
        ["git", "commit", "-m", "Auto-generated files [skip ci]"],
        capture_output=True,
        text=True,
    )
    if commit.returncode != 0:
        fail(f"git commit failed: {commit.stderr}")

    print("COMMIT CREATED")


def main() -> None:
    spec_path, spec = read_spec()
    print(f"USING SPEC {spec_path.as_posix()}")

    messages = build_messages(spec_path, spec)
    payload = call_openai(messages)
    validate_files(payload, spec)
    write_files(payload)
    git_commit_generated_files()

    print("BOOTSTRAP COMPLETE")


if __name__ == "__main__":
    main()
