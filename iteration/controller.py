from iteration.build import build_system
from iteration.runtime import start_server


def run_iteration_loop(spec: dict):
    print("=== CONTROLLER STARTED ===", flush=True)

    build = build_system(spec)
    print("=== BUILD RESULT ===", build, flush=True)

    runtime = start_server()
    print("=== RUNTIME RESULT ===", runtime, flush=True)

    result = {
        "build_id": "test_build",
        "message": "Build + runtime executed",
        "deployment_url": "http://localhost:8000",
        "logs": build.get("logs", []) + runtime.get("logs", []),
        "normalized_spec": spec,
    }

    print("=== FINAL RESULT ===", result, flush=True)

    return result


# 🔴 FORCE EXECUTION (NO __main__)
run_iteration_loop({})
