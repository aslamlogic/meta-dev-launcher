from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .spec_loader import AppSpec


class AppBuilder:
    def __init__(self, apps_dir: str = "apps/") -> None:
        self.apps_dir = Path(apps_dir)
        self.apps_dir.mkdir(parents=True, exist_ok=True)

    def build(self, spec: AppSpec) -> Dict[str, Any]:
        app_dir = self.apps_dir / spec.name
        app_dir.mkdir(parents=True, exist_ok=True)
        manifest = app_dir / "manifest.json"
        manifest.write_text(__import__("json").dumps(spec.raw, indent=2), encoding="utf-8")
        return {"app": spec.name, "built": True, "path": str(app_dir)}
