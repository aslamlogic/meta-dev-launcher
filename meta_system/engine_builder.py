from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


class EngineBuilder:
    def __init__(self, meta_system_dir: str = "meta_system/"):
        self.meta_system_dir = Path(meta_system_dir)
        self.meta_system_dir.mkdir(parents=True, exist_ok=True)

    def build(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        app_name = spec.get("name") or spec.get("app_name") or "app"
        artifact = self.meta_system_dir / f"{app_name}.engine.txt"
        artifact.write_text(f"engine built for: {app_name}\n", encoding="utf-8")
        return {"status": "built", "app": app_name, "artifact": str(artifact)}
