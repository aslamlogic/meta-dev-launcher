from pathlib import Path
import json


def load_app_specs(specs_dir: Path):
    specs = []
    if not specs_dir.exists():
        return specs

    for path in sorted(specs_dir.glob("*.json")):
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                data["_spec_path"] = str(path)
                specs.append(data)
    return specs
