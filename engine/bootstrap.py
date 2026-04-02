import json
import os
import sys
from pathlib import Path
import requests

CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"

SPEC_PATH = Path("specs/init.json")
GOAL_PATH = Path("goal.json")
QUEUE_PATH = Path("tasks/queue.json")
STATE_PATH = Path("tasks/state.json")

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
                        "content": {"type": "string"}
                    },
                    "required": ["path", "content"]
                }
            }
        },
        "required": ["files"]
    }
}


def fail(msg):
    print(f"ERROR: {msg}")
    sys.exit(1)


def read_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text())


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def read_spec():
    if not SPEC_PATH.exists():
        fail("Spec missing")
    return json.loads(SPEC_PATH.read_text())


def save_spec(spec):
    SPEC_PATH.write_text(json.dumps(spec, indent=2))


# -------- TASKS -------- #

def to_contract(spec):
    if "api" in spec:
        return spec

    eps = spec.get("endpoints", [])
    new_eps = []

    for ep in eps:
        new_eps.append({
            "name": ep.get("name", "endpoint"),
            "method": ep.get("method", "GET"),
            "path": ep.get("path", "/"),
            "response": {
                "type": "object",
                "schema": {
                    k: {"type": "string", "example": v}
                    for k, v in ep.get("response", {}).items()
                }
            }
        })

    return {
        "system": {"name": "meta", "type": "fastapi"},
        "api": {"endpoints": new_eps}
    }


def add_post_echo(spec):
    spec = to_contract(spec)

    if any(e["path"] == "/echo" for e in spec["api"]["endpoints"]):
        return spec

    spec["api"]["endpoints"].append({
        "name": "echo",
        "method": "POST",
        "path": "/echo",
        "request": {
            "type": "object",
            "schema": {
                "text": {"type": "string", "example": "hello"}
            }
        },
        "response": {
            "type": "object",
            "schema": {
                "echo": {"type": "string", "example": "hello"}
            }
        }
    })

    return spec


def apply_task(spec, task):
    if task == "add_post_echo":
        return add_post_echo(spec)
    if task == "strengthen_contract":
        return to_contract(spec)
    fail(f"Unknown task {task}")


# -------- GENERATION -------- #

def call_openai(spec):
    r = requests.post(
        CHAT_COMPLETIONS_URL,
        headers={
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
            "Content-Type": "application/json"
        },
        json={
            "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return ONLY JSON.\n"
                        "Generate EXACTLY:\n"
                        "main.py and requirements.txt.\n"
                        "No markdown."
                    )
                },
                {
                    "role": "user",
                    "content": json.dumps(spec)
                }
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": OUTPUT_SCHEMA
            },
            "temperature": 0
        }
    )

    if r.status_code != 200:
        fail(r.text)

    return json.loads(r.json()["choices"][0]["message"]["content"])


def validate(payload):
    files = payload.get("files", [])
    paths = [f["path"] for f in files]

    if "main.py" not in paths:
        fail("main.py missing")

    if "requirements.txt" not in paths:
        fail("requirements.txt missing")


def write_files(payload):
    for f in payload["files"]:
        Path(f["path"]).write_text(f["content"].strip() + "\n")
        print(f"WROTE {f['path']}")


# -------- MAIN LOOP -------- #

def main():
    spec = read_spec()
    goal = read_json(GOAL_PATH, {}).get("goal", "")

    queue = read_json(QUEUE_PATH, {"tasks": []})
    state = read_json(STATE_PATH, {
        "index": 0,
        "completed": []
    })

    # initialise tasks once
    if not queue["tasks"]:
        tasks = []
        if "post" in goal.lower():
            tasks.append("add_post_echo")
        tasks.append("strengthen_contract")

        queue = {"tasks": tasks}
        write_json(QUEUE_PATH, queue)

    idx = state["index"]
    tasks = queue["tasks"]

    # EXIT if done
    if idx >= len(tasks):
        print("ALL TASKS COMPLETE")
        return

    task = tasks[idx]

    # guard: skip if already done
    if task in state["completed"]:
        state["index"] += 1
        write_json(STATE_PATH, state)
        print("SKIPPING COMPLETED TASK")
        return

    print(f"APPLYING TASK: {task}")

    spec = apply_task(spec, task)
    save_spec(spec)

    payload = call_openai(spec)
    validate(payload)
    write_files(payload)

    # mark complete
    state["completed"].append(task)
    state["index"] += 1
    write_json(STATE_PATH, state)

    print("BOOTSTRAP COMPLETE")


if __name__ == "__main__":
    main()
