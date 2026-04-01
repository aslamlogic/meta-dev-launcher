from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from .engine_builder import EngineBuilder


class AppBuilder:
    def __init__(self, engine_builder: EngineBuilder | None = None):
        self.engine_builder = engine_builder or EngineBuilder()

    def build(self, app_name: str, build_spec: Dict[str, Any], output_dir: str | Path = "apps") -> Path:
        app_dir = self.engine_builder.build(app_name, build_spec, output_dir=output_dir)
        (app_dir / "app.txt").write_text(
            f"app {app_name} built\n",
            encoding="utf-8",
        )
        return app_dir
