from fastapi import FastAPI, Body
from iteration.controller import run_iteration_loop

app = FastAPI()


@app.get("/")
def root():
    return {"status": "ready"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run")
def run(spec: dict = Body(...)):
    print("[DEBUG SPEC RECEIVED]", spec)

    result = run_iteration_loop(spec)

    return result
