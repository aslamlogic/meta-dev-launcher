import os
from openai import OpenAI


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


SYSTEM_PROMPT = """
You are a deterministic software generator.

Given a JSON specification, you must generate a COMPLETE, runnable FastAPI application.

Rules:
- Output ONLY Python code
- No explanations
- No markdown
- No comments outside code
- Must include:
    - FastAPI app
    - /health endpoint
    - All endpoints defined in spec
- Code must be executable without modification
"""


def generate_code_openai(spec: dict) -> str:
    prompt = f"""
SPECIFICATION:
{spec}

Generate full FastAPI app now.
"""

    response = client.chat.completions.create(
        model="gpt-4.1",
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content
