from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List


@dataclass(frozen=True)
class AppSpec:
    name: str
    build: Dict[str, Any]
    deploy: Dict[str, Any]
    raw: Dict[str, Any]


class SpecLoader:
    def __init__(self, specs_dir: str | Path):
        self.specs_dir = Path(specs_dir)

    def load_all(self) -> List[AppSpec]:
        if not self.specs_dir.exists():
            return []
        specs: List[AppSpec] = []
        for path in sorted(self.specs_dir.glob("*.json")):
            with path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
            name = raw.get("name") or path.stem
            specs.append(
                AppSpec(
                    name=name,
                    build=raw.get("build", {}),
                    deploy=raw.get("deploy", {}),
                    raw=raw,
                )
            )
        return specs
