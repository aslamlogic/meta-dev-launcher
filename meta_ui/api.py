from fastapi import FastAPI
from pydantic import BaseModel
from iteration.controller import run_iteration_loop


app = FastAPI()


# ============================================================
# REQUEST MODEL
# ============================================================

class SpecRequest(BaseModel):
    spec: dict


# ============================================================
# DEFAULT SMR (GOVERNANCE BASELINE)
# ============================================================

DEFAULT_SMR = """
- System must produce valid Python code
- Must define a FastAPI app instance
- Must expose `app` as ASGI callable
- Must implement GET /health endpoint returning {'status': 'ok'}
- No placeholders, no pseudo-code
"""


# ============================================================
# ROUTES
# ============================================================

@app.get("/")
def root():
    return {"message": "Meta Dev Launcher running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run")
def run(spec_request: SpecRequest):
    """
    Executes full iteration loop
    """

    try:
        result = run_iteration_loop(
            spec_request.spec,
            DEFAULT_SMR
        )
        return result

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
