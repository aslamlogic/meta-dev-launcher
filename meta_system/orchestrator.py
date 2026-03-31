from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List

from meta_system.spec_loader import load_app_specs
from meta_system.app_builder import AppBuilder
from meta_system.engine_builder import EngineBuilder
from meta_system.deployer import Deployer
from meta_system.executor import Executor


class Orchestrator:
    def __init__(self, app_specs_dir: str = "specs/apps/", apps_dir: str = "apps/", meta_system_dir: str = "meta_system/"):
        self.app_specs_dir = app_specs_dir
        self.apps_dir = apps_dir
        self.meta_system_dir = meta_system_dir
        self.spec_loader = load_app_specs
        self.app_builder = AppBuilder(apps_dir=self.apps_dir)
        self.engine_builder = EngineBuilder(meta_system_dir=self.meta_system_dir)
        self.deployer = Deployer(apps_dir=self.apps_dir)
        self.executor = Executor()

    def run(self) -> Dict[str, Any]:
        specs = self.spec_loader(self.app_specs_dir)
        if not specs:
            return {"status": "noop", "message": "No app specs found."}

        results: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=min(32, max(1, len(specs)))) as pool:
            futures = {pool.submit(self._build_and_deploy, spec): spec for spec in specs}
            for future in as_completed(futures):
                results.append(future.result())

        return {"status": "ok", "results": results}

    def _build_and_deploy(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        app_name = spec.get("name") or spec.get("app_name") or "unknown_app"
        build_result = self.app_builder.build(spec)
        engine_result = self.engine_builder.build(spec)
        deploy_result = self.deployer.deploy(spec, build_result=build_result, engine_result=engine_result)
        execution_result = self.executor.execute(spec, build_result=build_result, engine_result=engine_result, deploy_result=deploy_result)
        return {
            "app": app_name,
            "build": build_result,
            "engine": engine_result,
            "deploy": deploy_result,
            "execution": execution_result,
        }


def main() -> None:
    orchestrator = Orchestrator(
        app_specs_dir=os.environ.get("APP_SPECS_DIR", "specs/apps/"),
        apps_dir=os.environ.get("APPS_DIR", "apps/"),
        meta_system_dir=os.environ.get("META_SYSTEM_DIR", "meta_system/"),
    )
    result = orchestrator.run()
    print(result)


if __name__ == "__main__":
    main()
