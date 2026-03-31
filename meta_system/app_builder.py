from pathlib import Path
import json


class AppBuilder:
    def __init__(self, apps_dir: Path):
        self.apps_dir = Path(apps_dir)

    def build(self, spec: dict):
        app_name = spec.get("name", "app")
        app_dir = self.apps_dir / app_name
        app_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "name": app_name,
            "spec": spec,
            "built": True,
        }
        manifest_path = app_dir / "build_manifest.json"
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return {
            "app_dir": str(app_dir),
            "manifest": str(manifest_path),
        }
