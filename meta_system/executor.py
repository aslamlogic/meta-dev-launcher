from __future__ import annotations

from typing import Any, Dict


class Executor:
    def execute(self, spec: Dict[str, Any], build_result: Dict[str, Any] | None = None, engine_result: Dict[str, Any] | None = None, deploy_result: Dict[str, Any] | None = None) -> Dict[str, Any]:
        app_name = spec.get("name") or spec.get("app_name") or "app"
        return {"status": "executed", "app": app_name, "build": build_result, "engine": engine_result, "deploy": deploy_result}
