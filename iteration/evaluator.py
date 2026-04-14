def build_prompt(spec: dict, smr: str) -> str:
    base_instruction = """
You are a deterministic software generator.

You MUST produce a valid FastAPI application.

STRICT REQUIREMENTS:
- Output ONLY code
- No explanations
- No markdown
- Must be directly executable
- The module must define `app = FastAPI()`
- The module must be self-contained and importable
- The module must implement every endpoint declared in the specification
- Each implemented endpoint must return JSON
""".strip()

    constraint_block = ""
    constraints = spec.get("constraints", [])

    if constraints:
        constraint_block += "\nMANDATORY CONSTRAINTS:\n"
        for c in constraints:
            constraint_block += f"- {c.get('instruction')}\n"

    spec_block = f"\nSPECIFICATION:\n{spec}\n"
    smr_block = f"\nGOVERNANCE RULES:\n{smr}\n"

    return base_instruction + constraint_block + spec_block + smr_block
