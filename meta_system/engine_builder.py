from pathlib import Path
import json


class EngineBuilder:
    def __init__(self, meta_system_dir: Path):
        self.meta_system_dir = Path(meta_system_dir)

    def build(self, spec: dict):
        engine_name = spec.get("name", "engine")
        engine_dir = self.meta_system_dir / "engines" / engine_name
        engine_dir.mkdir(parents=True, exist_ok=True)

        config = {
            "engine": engine_name,
            "source": spec.get("_spec_path"),
            "built": True,
        }
        config_path = engine_dir / "engine_config.json"
        with config_path.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        return {
            "engine_dir": str(engine_dir),
            "config": str(config_path),
        }
