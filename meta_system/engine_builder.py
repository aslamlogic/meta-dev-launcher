from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


class EngineBuilder:
    def build(self, app_name: str, build_spec: Dict[str, Any], output_dir: str | Path = "apps") -> Path:
        out = Path(output_dir) / app_name
        out.mkdir(parents=True, exist_ok=True)
        (out / "engine.txt").write_text(
            f"engine for {app_name}\nbuild_spec={build_spec}\n",
            encoding="utf-8",
        )
        return out
