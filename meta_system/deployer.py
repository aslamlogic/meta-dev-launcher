from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


class Deployer:
    def __init__(self, apps_dir: str = "apps/"):
        self.apps_dir = Path(apps_dir)
        self.apps_dir.mkdir(parents=True, exist_ok=True)

    def deploy(self, spec: Dict[str, Any], build_result: Dict[str, Any] | None = None, engine_result: Dict[str, Any] | None = None) -> Dict[str, Any]:
        app_name = spec.get("name") or spec.get("app_name") or "app"
        deploy_dir = self.apps_dir / app_name / "deploy"
        deploy_dir.mkdir(parents=True, exist_ok=True)
        marker = deploy_dir / "deployed.txt"
        marker.write_text("deployed\n", encoding="utf-8")
        return {"status": "deployed", "app": app_name, "marker": str(marker), "build": build_result, "engine": engine_result}
