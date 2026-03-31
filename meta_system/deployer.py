from pathlib import Path
import json


class Deployer:
    def __init__(self, apps_dir: Path):
        self.apps_dir = Path(apps_dir)

    def deploy(self, spec: dict, app_artifacts: dict, engine_artifacts: dict):
        app_name = spec.get("name", "app")
        deploy_dir = self.apps_dir / app_name / "deployment"
        deploy_dir.mkdir(parents=True, exist_ok=True)

        payload = {
            "app": app_name,
            "success": True,
            "app_artifacts": app_artifacts,
            "engine_artifacts": engine_artifacts,
        }
        deploy_path = deploy_dir / "deploy.json"
        with deploy_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        return {
            "success": True,
            "deployment_manifest": str(deploy_path),
        }
