import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from meta_system.spec_loader import load_app_specs
from meta_system.app_builder import AppBuilder
from meta_system.engine_builder import EngineBuilder
from meta_system.deployer import Deployer
from meta_system.executor import Executor


class Orchestrator:
    def __init__(self, specs_dir: str = "specs/apps/", meta_system_dir: str = "meta_system/", apps_dir: str = "apps/"):
        self.specs_dir = Path(specs_dir)
        self.meta_system_dir = Path(meta_system_dir)
        self.apps_dir = Path(apps_dir)
        self.app_builder = AppBuilder(self.apps_dir)
        self.engine_builder = EngineBuilder(self.meta_system_dir)
        self.deployer = Deployer(self.apps_dir)
        self.executor = Executor()

    def run(self):
        specs = load_app_specs(self.specs_dir)
        if not specs:
            return {"status": "ok", "message": "No app specs found.", "apps": []}

        self.apps_dir.mkdir(parents=True, exist_ok=True)
        self.meta_system_dir.mkdir(parents=True, exist_ok=True)

        results = []
        with ThreadPoolExecutor(max_workers=min(32, max(1, len(specs)))) as pool:
            futures = {
                pool.submit(self._build_and_deploy, spec): spec
                for spec in specs
            }
            for future in as_completed(futures):
                spec = futures[future]
                try:
                    results.append(future.result())
                except Exception as exc:
                    results.append({
                        "app": spec.get("name", "unknown"),
                        "status": "error",
                        "error": str(exc),
                    })

        return {"status": "ok", "apps": results}

    def _build_and_deploy(self, spec: dict):
        app_artifacts = self.app_builder.build(spec)
        engine_artifacts = self.engine_builder.build(spec)
        deploy_result = self.deployer.deploy(spec, app_artifacts, engine_artifacts)
        return {
            "app": spec.get("name", "unknown"),
            "status": "deployed" if deploy_result.get("success") else "built",
            "artifacts": {
                "app": app_artifacts,
                "engine": engine_artifacts,
            },
            "deploy": deploy_result,
        }


def main():
    orchestrator = Orchestrator()
    result = orchestrator.run()
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
