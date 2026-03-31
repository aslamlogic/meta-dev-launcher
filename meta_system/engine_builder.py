from __future__ import annotations

from pathlib import Path
from typing import Any, Dict


class EngineBuilder:
    def __init__(self, meta_system_dir: str = "meta_system/") -> None:
        self.meta_system_dir = Path(meta_system_dir)
        self.meta_system_dir.mkdir(parents=True, exist_ok=True)

    def build(self) -> Dict[str, Any]:
        bootstrap = self.meta_system_dir / "bootstrap.marker"
        bootstrap.write_text("use_existing_bootstrap=true\n", encoding="utf-8")
        return {"engine": "built", "bootstrap": str(bootstrap)}
