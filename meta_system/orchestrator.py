from __future__ import annotations

from typing import Any, Dict, List

from .app_builder import AppBuilder
from .deployer import Deployer
from .engine_builder import EngineBuilder
from .executor import Executor
from .spec_loader import SpecLoader


class Orchestrator:
    def __init__(self, app_specs_dir: str = "specs/apps/", apps_dir: str = "apps/", max_workers: int | None = None) -> None:
        self.loader = SpecLoader(app_specs_dir=app_specs_dir)
        self.engine_builder = EngineBuilder()
        self.app_builder = AppBuilder(apps_dir=apps_dir)
        self.deployer = Deployer(apps_dir=apps_dir)
        self.executor = Executor(max_workers=max_workers)

    def run(self) -> Dict[str, Any]:
        engine_result = self.engine_builder.build()
        specs = self.loader.load()

        built = self.executor.run_parallel(specs, self.app_builder.build)
        deployed = self.executor.run_parallel(specs, lambda spec: self.deployer.deploy(spec.name))

        return {
            "engine": engine_result,
            "built_apps": built,
            "deployed_apps": deployed,
            "multi_app_support": True,
            "parallel_execution": True,
        }


def main() -> None:
    Orchestrator().run()


if __name__ == "__main__":
    main()
