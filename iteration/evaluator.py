"""
iteration/evaluator.py

Deterministic validation engine
WITH backward compatibility for existing controller imports
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi.testclient import TestClient


# ============================================================
# 🔥 COMPATIBILITY LAYER (CRITICAL FIX)
# ============================================================

def evaluate_app(spec: Optional[Dict[str, Any]] = None, base_dir: str = ".") -> Dict[str, Any]:
    return run_validation(spec, base_dir)


def evaluate_system(spec: Optional[Dict[str, Any]] = None, base_dir: str = ".") -> Dict[str, Any]:
    return run_validation(spec, base_dir)


def validate_system(spec: Optional[Dict[str, Any]] = None, base_dir: str = ".") -> Dict[str, Any]:
    return run_validation(spec, base_dir)


# ============================================================
# MAIN VALIDATION
# ============================================================

def run_validation(spec: Optional[Dict[str, Any]] = None, base_dir: str = ".") -> Dict[str, Any]:

    repo_root = Path(base_dir).resolve()

    findings = []

    # ------------------------------------------------------------
    # LOAD APP
    # ------------------------------------------------------------
    load = load_app(repo_root)

    if not load["success"]:
        return fail(load["error_type"], load["error_message"])

    app = load["app"]

    # ------------------------------------------------------------
    # ROUTES
    # ------------------------------------------------------------
    routes = get_routes(app)

    # ------------------------------------------------------------
    # HEALTH CHECK
    # ------------------------------------------------------------
    if not route_exists(routes, "GET", "/health"):
        findings.append(finding("missing_route", "GET /health missing"))

    # ------------------------------------------------------------
    # RUNTIME TEST
    # ------------------------------------------------------------
    client = TestClient(app)

    try:
        r = client.get("/health")

        if r.status_code >= 400:
            findings.append(finding("runtime_error", f"/health returned {r.status_code}"))

    except Exception as e:
        findings.append(finding("runtime_error", str(e)))

    return {
        "overall_pass": len(findings) == 0,
        "validation_findings": findings,
        "findings": findings
    }


# ============================================================
# APP LOADING
# ============================================================

def load_app(repo_root: Path):

    sys.path.insert(0, str(repo_root))

    candidates = [
        "generated_app.main",
        "app.main",
        "main"
    ]

    for name in candidates:
        try:
            module = importlib.import_module(name)
            app = getattr(module, "app", None)

            if app:
                return {"success": True, "app": app}

        except Exception as e:
            last_error = e

    return {
        "success": False,
        "error_type": "import_error",
        "error_message": str(last_error)
    }


# ============================================================
# ROUTES
# ============================================================

def get_routes(app):

    routes = []

    for r in app.routes:
        if hasattr(r, "methods"):
            for m in r.methods:
                if m not in ["HEAD", "OPTIONS"]:
                    routes.append({
                        "method": m,
                        "path": r.path
                    })

    return routes


def route_exists(routes, method, path):
    return any(r["method"] == method and r["path"] == path for r in routes)


# ============================================================
# UTIL
# ============================================================

def finding(code, msg):
    return {
        "finding_code": code,
        "severity": "error",
        "message": msg
    }


def fail(t, msg):
    return {
        "overall_pass": False,
        "validation_findings": [
            {
                "finding_code": t,
                "severity": "error",
                "message": msg
            }
        ]
    }
