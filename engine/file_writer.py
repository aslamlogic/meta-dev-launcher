import os
import shutil


TARGET_DIR = "generated_app"


def reset_directory():
    if os.path.exists(TARGET_DIR):
        shutil.rmtree(TARGET_DIR)
    os.makedirs(TARGET_DIR, exist_ok=True)


def write_app(code: str):
    reset_directory()

    file_path = os.path.join(TARGET_DIR, "main.py")

    with open(file_path, "w") as f:
        f.write(code)

    return file_path
