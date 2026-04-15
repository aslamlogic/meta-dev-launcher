"""
meta_ui/api.py

Concurrent execution API for Meta Dev Launcher
"""

from fastapi import FastAPI
from threading import Thread
from typing import Dict, Any

from iteration.controller import run_iteration_loop
from iteration.run_registry import get_run, list_runs

app = FastAPI()

# ============================================================
# RUN LAUNCHER (ASYNC)
# ============================================================

@app.post("/run")
def start_run(payload: Dict[str, Any]):

    spec = payload.get("spec", {})
    project_id = payload.get("project_id", "default")

    # run in background
    thread = Thread(target=run_iteration_loop, args=(spec, project_id))
    thread.start()

    return {
        "status": "started",
        "message": "Run launched in background"
    }


# ============================================================
# RUN STATUS
# ============================================================

@app.get("/run/{run_id}")
def get_run_status(run_id: str):
    run = get_run(run_id)

    if not run:
        return {"error": "run not found"}

    return run


# ============================================================
# LIST RUNS
# ============================================================

@app.get("/runs")
def get_all_runs():
    return {"runs": list_runs()}


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():
    return {"status": "ok"}
