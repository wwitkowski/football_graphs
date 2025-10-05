from pathlib import Path
from typing import Any

import yaml


def get_config(path: Path) -> dict[str, Any]:
    """
    Load a YAML configuration file.

    Parameters
    ----------
    path : Path
        Path to the YAML configuration file.

    Returns
    -------
    dict of (str, Any)
        Parsed configuration data as a dictionary. Returns an empty
        dictionary if the file is valid but empty.

    Raises
    ------
    FileNotFoundError
        If the configuration file does not exist at the given path.
    RuntimeError
        If the file cannot be parsed as valid YAML.
    """
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found at {path}")
    except yaml.YAMLError as e:
        raise RuntimeError(f"Error parsing YAML config: {e}")
