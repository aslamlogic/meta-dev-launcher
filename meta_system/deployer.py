from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


class Deployer:
    def deploy(self, app_name: str, deploy_spec: Dict[str, Any], app_dir: str | Path) -> Dict[str, Any]:
        app_dir = Path(app_dir)
        marker = app_dir / "deployed.txt"
        marker.write_text(f"deployed {app_name}\ndeploy_spec={deploy_spec}\n", encoding="utf-8")
        return {"app": app_name, "status": "deployed", "path": str(app_dir)}
