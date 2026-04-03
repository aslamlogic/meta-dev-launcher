import subprocess
import time
import requests
import os
import signal


_current_process = None


def start_server():
    """
    Starts FastAPI server with proper cleanup and readiness check.
    """

    global _current_process

    logs = []

    # Kill previous process if exists
    if _current_process:
        try:
            os.kill(_current_process.pid, signal.SIGTERM)
            logs.append("Previous server stopped")
        except Exception:
            logs.append("No previous server to stop")

    process = subprocess.Popen(
        [
            "uvicorn",
            "generated_app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    _current_process = process

    # Wait for readiness
    for _ in range(10):
        try:
            r = requests.get("http://localhost:8000/health", timeout=2)
            if r.status_code == 200:
                logs.append("Server started successfully")
                return {
                    "status": "running",
                    "process_id": process.pid,
                    "logs": logs,
                }
        except Exception:
            time.sleep(1)

    process.kill()
    logs.append("Server failed to start")

    return {
        "status": "failed",
        "logs": logs,
    }
