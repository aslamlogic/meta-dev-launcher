import subprocess
import time
from engine.llm_interface import generate_code
from engine.file_writer import write_app


def run_app():
    process = subprocess.Popen(
        ["uvicorn", "generated_app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    time.sleep(3)
    return process


def build_system(spec: dict):
    print("Generating code from spec...")
    code = generate_code(spec)

    print("Writing files...")
    write_app(code)

    print("Starting application...")
    process = run_app()

    print("Application running.")
    return process
