import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate(spec_text, constraints, allowed_files):
    system_message = """
You are a deterministic code repair engine.

RULES:
- ONLY fix the listed failures
- ONLY modify allowed files
- DO NOT introduce new files
- DO NOT modify unrelated logic
- Output ONLY valid Python code
"""

    constraint_text = "\n".join([
        f"{c['failure_code']} → {c['constraint']}" for c in constraints
    ])

    user_message = f"""
SPEC:
{spec_text}

CONSTRAINTS:
{constraint_text}

ALLOWED FILES:
{allowed_files}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
    )

    return response.choices[0].message.content
