import json
from pathlib import Path

def load_from_json(file_path: str, filename: str):
    base_dir = Path(__file__).resolve().parents[1]

    folder_path = base_dir / file_path if file_path else base_dir / "resources"
    path = folder_path / filename

    if not path.exists():
        raise FileNotFoundError(f"Keyword file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)