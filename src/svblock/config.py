"""Configuration and theme loading for svblock."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from svblock.renderer.themes import BUILTIN_THEMES, THEME_DEFAULT

logger = logging.getLogger(__name__)


def load_theme(theme_name_or_path: str) -> dict[str, str]:
    """Load a theme by built-in name or from a file path.

    Built-in themes: default, dark, minimal, print.
    File themes: TOML or YAML files that map CSS variable names to values.
    Custom values are merged with the default theme (custom overrides).

    Args:
        theme_name_or_path: Built-in name or path to theme file.

    Returns:
        Complete theme dict (all CSS variables guaranteed present).
    """
    # Check built-in themes first
    if theme_name_or_path in BUILTIN_THEMES:
        return dict(BUILTIN_THEMES[theme_name_or_path])

    # Try loading from file
    path = Path(theme_name_or_path)
    if not path.exists():
        logger.warning(
            "Theme '%s' not found, using default", theme_name_or_path
        )
        return dict(THEME_DEFAULT)

    custom = _load_theme_file(path)

    # Warn on unknown keys
    known_keys = set(THEME_DEFAULT.keys())
    for key in custom:
        if key not in known_keys:
            logger.warning("Unknown theme variable: %s", key)

    # Merge: default as base, custom overrides
    merged = dict(THEME_DEFAULT)
    merged.update(custom)
    return merged


def _load_theme_file(path: Path) -> dict[str, str]:
    """Load theme variables from a TOML or YAML file."""
    suffix = path.suffix.lower()
    text = path.read_text(encoding="utf-8")

    if suffix in (".toml",):
        return _load_toml(text)
    if suffix in (".yaml", ".yml"):
        return _load_yaml(text)

    # Try TOML first, fall back to YAML
    try:
        return _load_toml(text)
    except Exception:
        return _load_yaml(text)


def _load_toml(text: str) -> dict[str, str]:
    """Parse TOML text into a flat string dict."""
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError as e:
            raise ImportError(
                "TOML support on Python 3.10 requires 'tomli'. "
                "Install with: pip install tomli"
            ) from e

    data = tomllib.loads(text)
    # Flatten: support both flat and nested [theme] table
    if "theme" in data and isinstance(data["theme"], dict):
        data = data["theme"]
    return {k: str(v) for k, v in data.items()}


def _load_yaml(text: str) -> dict[str, str]:
    """Parse YAML text into a flat string dict."""
    try:
        import yaml
    except ImportError as e:
        raise ImportError(
            "YAML theme support requires 'pyyaml'. "
            "Install with: pip install pyyaml"
        ) from e

    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        return {}
    # Flatten: support both flat and nested 'theme' key
    if "theme" in data and isinstance(data["theme"], dict):
        data = data["theme"]
    return {k: str(v) for k, v in data.items()}
