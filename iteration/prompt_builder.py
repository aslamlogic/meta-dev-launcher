def build_prompt(spec: dict, smr: str) -> str:
    """
    Deterministic prompt construction with enforced constraints.
    """

    base_instruction = """
You are a deterministic software generator.

You MUST produce a valid FastAPI application.

STRICT REQUIREMENTS:
- Output ONLY code
- No explanations
- No markdown
- Must be directly executable
"""

    # ============================================================
    # CRITICAL: INJECT CONSTRAINTS
    # ============================================================
    constraint_block = ""

    constraints = spec.get("constraints", [])

    if constraints:
        constraint_block += "\nMANDATORY CONSTRAINTS:\n"
        for c in constraints:
            constraint_block += f"- {c.get('instruction')}\n"

    # ============================================================
    # SPEC BLOCK
    # ============================================================
    spec_block = f"\nSPECIFICATION:\n{spec}\n"

    # ============================================================
    # SMR BLOCK
    # ============================================================
    smr_block = f"\nGOVERNANCE RULES:\n{smr}\n"

    return base_instruction + constraint_block + spec_block + smr_block
