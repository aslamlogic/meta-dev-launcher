import subprocess
import time
import requests
import random


def start_server():
    """
    Starts FastAPI server on a dynamic port to avoid collisions.
    """

    logs = []

    port = random.randint(8000, 9000)
    base_url = f"http://localhost:{port}"

    process = subprocess.Popen(
        [
            "uvicorn",
            "generated_app.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for readiness
    for _ in range(10):
        try:
            r = requests.get(f"{base_url}/health", timeout=2)
            if r.status_code == 200:
                logs.append(f"Server started on port {port}")
                return {
                    "status": "running",
                    "base_url": base_url,
                    "process_id": process.pid,
                    "logs": logs,
                }
        except Exception:
            time.sleep(1)

    logs.append("Server failed to start")

    return {
        "status": "failed",
        "logs": logs,
    }
