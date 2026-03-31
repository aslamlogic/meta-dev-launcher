from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def load_app_specs(specs_dir: str) -> List[Dict[str, Any]]:
    base = Path(specs_dir)
    if not base.exists():
        return []

    specs: List[Dict[str, Any]] = []
    for path in sorted(base.rglob("*.json")):
        try:
            specs.append(json.loads(path.read_text(encoding="utf-8")))
        except Exception:
            continue
    return specs
