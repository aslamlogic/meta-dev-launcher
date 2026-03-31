import os
import json
import requests

API_URL = "https://api.anthropic.com/v1/messages"


def call_claude(prompt):
    r = requests.post(
        API_URL,
        headers={
            "x-api-key": os.getenv("CLAUDE_API_KEY"),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-3-5-sonnet-20240620",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}],
        },
    )

    try:
        data = r.json()
        if "content" in data:
            text = data["content"][0].get("text", "")
            return json.loads(text)
    except:
        pass

    return {"files": []}


def main():
    with open("specs/init.json") as f:
        spec = json.load(f)

    prompt = f"""You are a senior software engineer.

Generate a COMPLETE working Python FastAPI application.

Return ONLY valid JSON in this exact format:

{{
  "files": [
    {{
      "path": "main.py",
      "content": "full python code"
    }},
    {{
      "path": "requirements.txt",
      "content": "dependencies"
    }}
  ]
}}

System specification:
{json.dumps(spec, indent=2)}
"""

    result = call_claude(prompt)

    for f in result.get("files", []):
        os.makedirs(os.path.dirname(f["path"]) or ".", exist_ok=True)
        with open(f["path"], "w") as file:
            file.write(f["content"])


if __name__ == "__main__":
    main()
