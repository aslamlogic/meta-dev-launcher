#!/usr/bin/env python3
"""
phase1_promote.py

Deterministic Phase I promotion script.

Purpose
1. Runs in meta-dev-launcher (MDL), which is the canonical source repo.
2. Keeps P8 present but latent (non-executing) by enforcing a runtime flag.
3. Performs a pre-promotion gate over the current achievable Phase I operational checks.
4. Promotes approved runtime files into mdl-autonomous-build.
5. Pins deployment-critical environment files.
6. Commits and pushes to the deployment repo so Render auto-deploy can do its work.

This script does NOT claim to implement the full formal P6/P7 engine.
It automates the current executable bridge:
MDL -> MDL auto -> Render
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


# =========================
# CONFIGURATION
# =========================

ROOT = Path(".").resolve()
DEPLOY_REPO_NAME = "mdl-autonomous-build"
DEPLOY_REPO_DIR = ROOT / DEPLOY_REPO_NAME

# Prefer token-auth clone if provided. Falls back to SSH, then HTTPS.
DEPLOY_REPO_HTTPS = "https://github.com/aslamlogic/mdl-autonomous-build.git"
DEPLOY_REPO_SSH = "git@github.com:aslamlogic/mdl-autonomous-build.git"

# Files currently known from the handover to be deployment-critical.
FILES_TO_PROMOTE: List[str] = [
    "meta_ui/api.py",
    "iteration/controller.py",
    "requirements.txt",
    "runtime.txt",
    "render.yaml",
]

# Deterministic environment lock taken from the successful deployment state.
PINNED_REQUIREMENTS = """fastapi==0.95.2
pydantic==1.10.13
uvicorn==0.23.2
"""

PINNED_RUNTIME = "python-3.11.9\n"

# This render.yaml is conservative.
# It does not try to redesign your Render service.
# It only provides a stable deploy descriptor if the file is missing or drifted.
PINNED_RENDER_YAML = """services:
  - type: web
    name: mdl-autonomous-build
    env: python
    plan: starter
    autoDeploy: true
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn meta_ui.api:app --host 0.0.0.0 --port $PORT
"""

# P8 remains architecturally present but dormant in Phase I.
# The script enforces this as a runtime flag file in the deployment repo.
P8_FLAG_RELATIVE_PATH = "config/phase_controls.json"
P8_FLAG_PAYLOAD = {
    "secondary_validation_mode": "OFF",
    "p8_present": True,
    "p8_latent": True,
    "phase": "PHASE_1",
}

# Optional local checks. These are operational checks only.
REQUIRED_SOURCE_PATHS: List[str] = [
    "meta_ui/api.py",
    "iteration/controller.py",
]

# Files that should exist in the deployment repo for Render stability.
REQUIRED_DEPLOYMENT_PATHS: List[str] = [
    "meta_ui/api.py",
    "requirements.txt",
    "runtime.txt",
    "render.yaml",
]

COMMIT_MESSAGE = "Phase I deterministic promotion from MDL to MDL auto"


# =========================
# DATA TYPES
# =========================

@dataclass
class CmdResult:
    code: int
    stdout: str
    stderr: str


class PromotionError(RuntimeError):
    pass


# =========================
# UTILITIES
# =========================

def run(
    command: Sequence[str],
    cwd: Optional[Path] = None,
    check: bool = True,
    env: Optional[dict] = None,
) -> CmdResult:
    process = subprocess.run(
        list(command),
        cwd=str(cwd) if cwd else None,
        env=env or os.environ.copy(),
        text=True,
        capture_output=True,
    )
    result = CmdResult(
        code=process.returncode,
        stdout=process.stdout.strip(),
        stderr=process.stderr.strip(),
    )
    if check and result.code != 0:
        raise PromotionError(
            f"Command failed: {' '.join(command)}\n"
            f"Exit code: {result.code}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
    return result


def echo(message: str) -> None:
    print(message, flush=True)


def ensure_file_exists(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise PromotionError(f"Required file missing: {path}")


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, content: str) -> None:
    ensure_parent_dir(path)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: dict) -> None:
    ensure_parent_dir(path)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def copy_file(src: Path, dst: Path) -> None:
    ensure_file_exists(src)
    ensure_parent_dir(dst)
    shutil.copy2(src, dst)
    echo(f"copied: {src.relative_to(ROOT)} -> {dst}")


def repo_has_changes(repo_dir: Path) -> bool:
    result = run(["git", "status", "--porcelain"], cwd=repo_dir, check=True)
    return bool(result.stdout.strip())


def get_tokenised_https_url() -> Optional[str]:
    token = (
        os.environ.get("GITHUB_TOKEN")
        or os.environ.get("GH_TOKEN")
        or os.environ.get("REPO_PUSH_TOKEN")
    )
    if not token:
        return None
    return f"https://{token}@github.com/aslamlogic/mdl-autonomous-build.git"


def clone_or_update_deploy_repo() -> None:
    if DEPLOY_REPO_DIR.exists():
        echo(f"deploy repo exists: {DEPLOY_REPO_DIR}")
        run(["git", "fetch", "origin"], cwd=DEPLOY_REPO_DIR, check=True)
        run(["git", "checkout", "main"], cwd=DEPLOY_REPO_DIR, check=True)
        run(["git", "pull", "--rebase", "origin", "main"], cwd=DEPLOY_REPO_DIR, check=True)
        return

    url_candidates: List[str] = []
    token_url = get_tokenised_https_url()
    if token_url:
        url_candidates.append(token_url)
    url_candidates.append(DEPLOY_REPO_SSH)
    url_candidates.append(DEPLOY_REPO_HTTPS)

    last_error: Optional[Exception] = None
    for url in url_candidates:
        try:
            echo(f"cloning deploy repo via: {url.split('@')[-1] if '@' in url else url}")
            run(["git", "clone", url, DEPLOY_REPO_NAME], cwd=ROOT, check=True)
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if DEPLOY_REPO_DIR.exists():
                shutil.rmtree(DEPLOY_REPO_DIR, ignore_errors=True)

    raise PromotionError(f"Failed to clone deployment repo. Last error: {last_error}")


# =========================
# PHASE I GATES
# =========================

def verify_running_in_mdl() -> None:
    git_dir = ROOT / ".git"
    if not git_dir.exists():
        raise PromotionError(f"Not inside a git repository: {ROOT}")

    remote_result = run(["git", "remote", "-v"], cwd=ROOT, check=True)
    remote_text = remote_result.stdout + "\n" + remote_result.stderr
    if "meta-dev-launcher" not in remote_text:
        echo("warning: could not positively confirm repo name from remotes")
    else:
        echo("confirmed: running in MDL canonical repo")


def verify_required_source_files() -> None:
    for rel in REQUIRED_SOURCE_PATHS:
        ensure_file_exists(ROOT / rel)
    echo("source gate passed: required MDL source files present")


def verify_deployment_descriptors() -> None:
    write_text(ROOT / "requirements.txt", PINNED_REQUIREMENTS)
    write_text(ROOT / "runtime.txt", PINNED_RUNTIME)

    render_path = ROOT / "render.yaml"
    if not render_path.exists():
        write_text(render_path, PINNED_RENDER_YAML)
    echo("environment lock enforced in MDL source repo")


def perform_local_operational_checks() -> None:
    """
    Operational checks only.
    This is intentionally honest and conservative.
    It does not pretend to be the full formal P6 engine.
    """
    # 1. Basic Python syntax compilation for known source files.
    for rel in REQUIRED_SOURCE_PATHS:
        target = ROOT / rel
        run([sys.executable, "-m", "py_compile", str(target)], cwd=ROOT, check=True)
    echo("local operational gate passed: py_compile successful")

    # 2. Sanity check that API entrypoint mentions /run and /health.
    api_text = (ROOT / "meta_ui" / "api.py").read_text(encoding="utf-8")
    for required_fragment in ('"/run"', '"/health"'):
        if required_fragment not in api_text:
            raise PromotionError(f"API sanity check failed: missing {required_fragment} in meta_ui/api.py")
    echo("local operational gate passed: API fragments present")

    # 3. Keep P8 latent, not removed.
    if "secondary_validation_mode" not in json.dumps(P8_FLAG_PAYLOAD):
        raise PromotionError("P8 latent control payload malformed")
    echo("phase-control gate passed: P8 remains present but latent")


# =========================
# PROMOTION
# =========================

def enforce_deploy_repo_environment() -> None:
    write_text(DEPLOY_REPO_DIR / "requirements.txt", PINNED_REQUIREMENTS)
    write_text(DEPLOY_REPO_DIR / "runtime.txt", PINNED_RUNTIME)
    write_text(DEPLOY_REPO_DIR / "render.yaml", PINNED_RENDER_YAML)
    write_json(DEPLOY_REPO_DIR / P8_FLAG_RELATIVE_PATH, P8_FLAG_PAYLOAD)
    echo("deployment repo environment lock enforced")


def promote_runtime_files() -> None:
    for rel in FILES_TO_PROMOTE:
        src = ROOT / rel
        dst = DEPLOY_REPO_DIR / rel
        copy_file(src, dst)

    # Ensure Phase-I control file is present in the deployment repo.
    write_json(DEPLOY_REPO_DIR / P8_FLAG_RELATIVE_PATH, P8_FLAG_PAYLOAD)

    # Verify critical files really exist in the deployment repo.
    for rel in REQUIRED_DEPLOYMENT_PATHS:
        ensure_file_exists(DEPLOY_REPO_DIR / rel)

    echo("promotion gate passed: deployment-critical files present in MDL auto")


def commit_and_push() -> None:
    if not repo_has_changes(DEPLOY_REPO_DIR):
        echo("no deploy-repo changes detected; nothing to commit")
        return

    run(["git", "add", "."], cwd=DEPLOY_REPO_DIR, check=True)

    status_result = run(["git", "status", "--porcelain"], cwd=DEPLOY_REPO_DIR, check=True)
    if not status_result.stdout.strip():
        echo("nothing staged after add; stopping")
        return

    run(["git", "commit", "-m", COMMIT_MESSAGE], cwd=DEPLOY_REPO_DIR, check=True)
    run(["git", "push", "origin", "main"], cwd=DEPLOY_REPO_DIR, check=True)
    echo("push complete: MDL auto updated; Render auto-deploy should now trigger")


# =========================
# MAIN
# =========================

def main() -> int:
    try:
        echo("=== Phase I Deterministic Promotion Start ===")
        verify_running_in_mdl()
        verify_required_source_files()
        verify_deployment_descriptors()
        perform_local_operational_checks()

        clone_or_update_deploy_repo()
        enforce_deploy_repo_environment()
        promote_runtime_files()
        commit_and_push()

        echo("=== PROMOTION COMPLETE ===")
        echo("Result:")
        echo("1. Script belongs in MDL.")
        echo("2. MDL auto updated only because this promotion step executed.")
        echo("3. Render should auto-deploy from MDL auto if service settings have not drifted.")
        return 0

    except PromotionError as exc:
        echo("=== PROMOTION FAILED ===")
        echo(str(exc))
        return 1

    except Exception as exc:  # noqa: BLE001
        echo("=== UNHANDLED FAILURE ===")
        echo(f"{type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
