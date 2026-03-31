from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


class AppBuilder:
    def __init__(self, apps_dir: str = "apps/"):
        self.apps_dir = Path(apps_dir)
        self.apps_dir.mkdir(parents=True, exist_ok=True)

    def build(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        app_name = spec.get("name") or spec.get("app_name") or "app"
        app_dir = self.apps_dir / app_name
        app_dir.mkdir(parents=True, exist_ok=True)
        artifact = app_dir / "build.txt"
        artifact.write_text(f"built app: {app_name}\n", encoding="utf-8")
        return {"status": "built", "app": app_name, "artifact": str(artifact)}
