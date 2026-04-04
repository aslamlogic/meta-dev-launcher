import os
from openai import OpenAI

def _get_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    return OpenAI(api_key=api_key)


def generate_code(spec: dict) -> str:
    client = _get_client()

    prompt = f"""
Generate a minimal FastAPI app.

Requirements:
- Must define: app = FastAPI()
- Must include GET /health endpoint
- Must return JSON

Spec:
{spec}

Return ONLY Python code.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {"role": "system", "content": "You generate valid Python FastAPI code only."},
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("LLM returned empty response")

    return content
