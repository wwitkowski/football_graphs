from pathlib import Path
from typing import Any

import yaml


def get_config(path: Path) -> dict[str, Any]:
    """Load YAML config (e.g., list of leagues)."""
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found at {path}")
    except yaml.YAMLError as e:
        raise RuntimeError(f"Error parsing YAML config: {e}")
