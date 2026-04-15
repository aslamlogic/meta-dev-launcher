"""
iteration/file_writer.py

Deterministic file output system for the Meta Dev Launcher.

Purpose
-------
1. Persist generated file bundles to a controlled repository subtree.
2. Prevent path traversal and forbidden writes.
3. Remove stale generated output before writing a new candidate.
4. Verify that the written manifest matches the expected bundle.

Supported bundle shape
----------------------
The writer accepts either:
1. A dict with a "files" array:
   {
     "files": [
       {"path": "generated_app/main.py", "content": "..."}
     ]
   }

2. A raw list of file objects:
   [
     {"path": "generated_app/main.py", "content": "..."}
   ]

Write policy
------------
- Only relative paths are allowed.
- Writes are restricted to approved roots.
- Existing output trees can be removed before a new write.
- Parent directories are created automatically.
- A manifest is returned after write for downstream validation/audit.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_ALLOWED_ROOTS = (
    "generated_app",
    "frontend",
    "app",
    "src",
    "tests",
    "config",
)

DEFAULT_CLEAN_ROOTS = (
    "generated_app",
    "frontend",
    "app",
    "src",
    "tests",
)


# ============================================================
# PUBLIC API
# ============================================================

def write_files(bundle: Any, base_dir: str = ".") -> Dict[str, Any]:
    """
    Backward-compatible entrypoint for controller flows.

    Parameters
    ----------
    bundle:
        Either {"files": [...]} or a raw list of {"path", "content"} objects.
    base_dir:
        Repository root against which all relative file paths are resolved.

    Returns
    -------
    Dict[str, Any]
        {
          "success": bool,
          "written_files": [...],
          "file_count": int,
          "base_dir": str,
          "error_type": str | None,
          "error_message": str | None,
          "diagnostics": {...}
        }
    """
    return write_bundle(bundle=bundle, base_dir=base_dir)


def write_bundle(bundle: Any, base_dir: str = ".") -> Dict[str, Any]:
    """
    Full write pipeline.

    Flow
    ----
    1. Normalize bundle.
    2. Validate every path.
    3. Clean previous generated roots.
    4. Write files deterministically.
    5. Verify written manifest.
    """
    repo_root = Path(base_dir).resolve()

    normalized_files, error = _normalize_bundle(bundle)
    if error is not None:
        return _failure(
            error_type="bundle_normalization_failure",
            error_message=error,
            base_dir=str(repo_root),
            diagnostics={"stage": "normalize_bundle"},
        )

    path_error = _validate_paths(normalized_files)
    if path_error is not None:
        return _failure(
            error_type="path_validation_failure",
            error_message=path_error,
            base_dir=str(repo_root),
            diagnostics={"stage": "validate_paths"},
        )

    clean_result = prepare_output_dir(base_dir=str(repo_root))
    if not clean_result["success"]:
        return clean_result

    write_result = _write_normalized_files(normalized_files, repo_root)
    if not write_result["success"]:
        return write_result

    verify_error = verify_files_present(normalized_files, repo_root)
    if verify_error is not None:
        return _failure(
            error_type="manifest_verification_failure",
            error_message=verify_error,
            base_dir=str(repo_root),
            diagnostics={"stage": "verify_manifest"},
        )

    written_files = write_result["written_files"]

    return {
        "success": True,
        "written_files": written_files,
        "file_count": len(written_files),
        "base_dir": str(repo_root),
        "error_type": None,
        "error_message": None,
        "diagnostics": {
            "stage": "complete",
            "paths": [item["path"] for item in written_files],
        },
    }


def prepare_output_dir(base_dir: str = ".") -> Dict[str, Any]:
    """
    Remove configured generated roots before a new candidate is written.

    This prevents stale files from leaking into the next candidate.
    """
    repo_root = Path(base_dir).resolve()

    try:
        removed: List[str] = []

        for root_name in DEFAULT_CLEAN_ROOTS:
            target = (repo_root / root_name).resolve()

            if not _is_within_repo(repo_root, target):
                return _failure(
                    error_type="unsafe_clean_target",
                    error_message=f"Refusing to clean path outside repo: {target}",
                    base_dir=str(repo_root),
                    diagnostics={"stage": "prepare_output_dir", "target": str(target)},
                )

            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                    removed.append(str(target.relative_to(repo_root)))
                else:
                    target.unlink()
                    removed.append(str(target.relative_to(repo_root)))

        return {
            "success": True,
            "removed_roots": removed,
            "base_dir": str(repo_root),
            "error_type": None,
            "error_message": None,
            "diagnostics": {"stage": "prepare_output_dir"},
        }

    except Exception as exc:
        return _failure(
            error_type="output_dir_prepare_failure",
            error_message=str(exc),
            base_dir=str(repo_root),
            diagnostics={
                "stage": "prepare_output_dir",
                "exception_class": exc.__class__.__name__,
            },
        )


def verify_files_present(files: List[Dict[str, str]], base_dir: Path) -> Optional[str]:
    """
    Ensure every file in the normalized bundle exists on disk and matches content.
    """
    for item in files:
        rel_path = item["path"]
        expected_content = item["content"]
        abs_path = (base_dir / rel_path).resolve()

        if not abs_path.exists():
            return f"Expected file is missing after write: {rel_path}"

        if not abs_path.is_file():
            return f"Expected path is not a file after write: {rel_path}"

        actual_content = abs_path.read_text(encoding="utf-8")
        if actual_content != expected_content:
            return f"Written file content mismatch: {rel_path}"

    return None


# ============================================================
# INTERNAL WRITE ENGINE
# ============================================================

def _write_normalized_files(files: List[Dict[str, str]], repo_root: Path) -> Dict[str, Any]:
    written_files: List[Dict[str, Any]] = []

    try:
        for item in files:
            rel_path = item["path"]
            content = item["content"]

            abs_path = (repo_root / rel_path).resolve()

            if not _is_within_repo(repo_root, abs_path):
                return _failure(
                    error_type="path_escape_detected",
                    error_message=f"Resolved path escapes repository root: {rel_path}",
                    base_dir=str(repo_root),
                    diagnostics={"stage": "write_file", "path": rel_path},
                )

            abs_path.parent.mkdir(parents=True, exist_ok=True)
            abs_path.write_text(content, encoding="utf-8")

            written_files.append(
                {
                    "path": rel_path,
                    "bytes": len(content.encode("utf-8")),
                    "sha256": _sha256_text(content),
                }
            )

        return {
            "success": True,
            "written_files": written_files,
            "file_count": len(written_files),
            "base_dir": str(repo_root),
            "error_type": None,
            "error_message": None,
            "diagnostics": {"stage": "write_files"},
        }

    except Exception as exc:
        return _failure(
            error_type="file_write_failure",
            error_message=str(exc),
            base_dir=str(repo_root),
            diagnostics={
                "stage": "write_files",
                "exception_class": exc.__class__.__name__,
            },
        )


# ============================================================
# NORMALIZATION
# ============================================================

def _normalize_bundle(bundle: Any) -> Tuple[List[Dict[str, str]], Optional[str]]:
    if isinstance(bundle, dict):
        if "files" not in bundle:
            return [], "Bundle dict must contain a 'files' key"
        raw_files = bundle["files"]
    elif isinstance(bundle, list):
        raw_files = bundle
    else:
        return [], "Bundle must be either a dict with 'files' or a list of file objects"

    if not isinstance(raw_files, list):
        return [], "'files' must be a list"

    normalized: List[Dict[str, str]] = []

    for index, item in enumerate(raw_files):
        if not isinstance(item, dict):
            return [], f"files[{index}] must be an object"

        path = item.get("path")
        content = item.get("content")

        if not isinstance(path, str) or not path.strip():
            return [], f"files[{index}].path must be a non-empty string"

        if not isinstance(content, str):
            return [], f"files[{index}].content must be a string"

        normalized.append(
            {
                "path": _normalize_relative_path(path),
                "content": content,
            }
        )

    normalized = _deduplicate_by_path_last_write_wins(normalized)

    if not normalized:
        return [], "Bundle contains zero normalized files"

    return normalized, None


def _normalize_relative_path(path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    normalized = normalized.lstrip("/")
    return normalized


def _deduplicate_by_path_last_write_wins(files: List[Dict[str, str]]) -> List[Dict[str, str]]:
    latest_by_path: Dict[str, Dict[str, str]] = {}
    order: List[str] = []

    for item in files:
        path = item["path"]
        if path not in latest_by_path:
            order.append(path)
        latest_by_path[path] = item

    return [latest_by_path[path] for path in order]


# ============================================================
# PATH SAFETY
# ============================================================

def _validate_paths(files: List[Dict[str, str]]) -> Optional[str]:
    for item in files:
        path = item["path"]

        if not path:
            return "Empty file path is not allowed"

        if path.startswith("/"):
            return f"Absolute path is forbidden: {path}"

        if path == "." or path == "..":
            return f"Invalid relative path: {path}"

        path_parts = Path(path).parts

        if any(part in ("..", "") for part in path_parts):
            return f"Path traversal or invalid segment detected: {path}"

        if _contains_forbidden_segment(path_parts):
            return f"Forbidden repository segment detected: {path}"

        if not _is_allowed_root(path_parts):
            return f"Write path is outside approved roots: {path}"

    return None


def _contains_forbidden_segment(parts: Tuple[str, ...]) -> bool:
    forbidden = {
        ".git",
        ".github",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        "node_modules",
    }
    return any(part in forbidden for part in parts)


def _is_allowed_root(parts: Tuple[str, ...]) -> bool:
    if not parts:
        return False
    return parts[0] in DEFAULT_ALLOWED_ROOTS


def _is_within_repo(repo_root: Path, target: Path) -> bool:
    try:
        target.relative_to(repo_root)
        return True
    except ValueError:
        return False


# ============================================================
# UTILITIES
# ============================================================

def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _failure(
    error_type: str,
    error_message: str,
    base_dir: str,
    diagnostics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "success": False,
        "written_files": [],
        "file_count": 0,
        "base_dir": base_dir,
        "error_type": error_type,
        "error_message": error_message,
        "diagnostics": diagnostics or {},
    }


# ============================================================
# OPTIONAL DEBUG ENTRYPOINT
# ============================================================

if __name__ == "__main__":
    sample_bundle = {
        "files": [
            {
                "path": "generated_app/__init__.py",
                "content": "",
            },
            {
                "path": "generated_app/main.py",
                "content": (
                    "from fastapi import FastAPI\n\n"
                    "app = FastAPI()\n\n"
                    "@app.get('/health')\n"
                    "def health():\n"
                    "    return {'status': 'ok'}\n"
                ),
            },
        ]
    }

    result = write_bundle(sample_bundle, base_dir=".")
    print(json.dumps(result, indent=2))
