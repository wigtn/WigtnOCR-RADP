"""YAML configuration loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_yaml_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML config file.

    Args:
        path: Absolute or repo-root-relative path to the YAML file.

    Returns:
        Parsed config as dict.
    """
    p = Path(path)
    if not p.is_absolute():
        p = resolve_config_path(p)
    with p.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_config_path(path: str | Path) -> Path:
    """Resolve a config path relative to the repo root.

    The repo root is identified by the presence of pyproject.toml.
    """
    p = Path(path)
    if p.is_absolute():
        return p
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / "pyproject.toml").exists():
            return parent / p
    return cwd / p
