from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


class Deployer:
    def __init__(self, apps_dir: str = "apps/") -> None:
        self.apps_dir = Path(apps_dir)

    def deploy(self, app_name: str) -> Dict[str, Any]:
        app_dir = self.apps_dir / app_name
        status = app_dir / "deployed.marker"
        status.write_text("deployed=true\n", encoding="utf-8")
        return {"app": app_name, "deployed": True, "path": str(app_dir)}
