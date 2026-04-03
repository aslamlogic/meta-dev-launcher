import subprocess
import time
import requests


_current_process = None


def start_server():
    """
    Starts FastAPI server safely and ensures readiness.
    Compatible with GitHub Actions.
    """

    global _current_process
    logs = []

    # Stop previous process safely
    if _current_process:
        try:
            _current_process.terminate()
            _current_process.wait(timeout=3)
            logs.append("Previous server terminated")
        except Exception:
            logs.append("Previous server termination skipped")

    process = subprocess.Popen(
        [
            "uvicorn",
            "generated_app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            "8000",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
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

    # Cleanup if failed
    try:
        process.terminate()
    except Exception:
        pass

    logs.append("Server failed to start")

    return {
        "status": "failed",
        "logs": logs,
    }
