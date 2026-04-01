from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List

from .app_builder import AppBuilder
from .deployer import Deployer
from .executor import Executor
from .spec_loader import AppSpec, SpecLoader


class Orchestrator:
    def __init__(self, specs_dir: str | Path = "specs/apps", output_dir: str | Path = "apps"):
        self.specs_dir = Path(specs_dir)
        self.output_dir = Path(output_dir)
        self.loader = SpecLoader(self.specs_dir)
        self.builder = AppBuilder()
        self.deployer = Deployer()
        self.executor = Executor()

    def _process_one(self, spec: AppSpec) -> Dict[str, Any]:
        app_dir = self.builder.build(spec.name, spec.build, output_dir=self.output_dir)
        deploy_result = self.deployer.deploy(spec.name, spec.deploy, app_dir)
        return {"spec": asdict(spec), "app_dir": str(app_dir), "deploy": deploy_result}

    def run(self, parallel: bool = True) -> List[Dict[str, Any]]:
        specs = self.loader.load_all()
        if parallel:
            return self.executor.run_parallel(specs, self._process_one)
        return [self._process_one(spec) for spec in specs]


def main() -> None:
    Orchestrator().run(parallel=True)


if __name__ == "__main__":
    main()
