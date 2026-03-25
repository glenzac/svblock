"""Tests for theme loading and built-in themes."""

from __future__ import annotations

import tempfile

from svblock.config import load_theme
from svblock.renderer.themes import BUILTIN_THEMES, THEME_DEFAULT


class TestBuiltinThemes:
    def test_load_default(self) -> None:
        theme = load_theme("default")
        assert theme["--sym-bg"] == "#ffffff"

    def test_load_dark(self) -> None:
        theme = load_theme("dark")
        assert theme["--sym-bg"] != "#ffffff"

    def test_load_minimal(self) -> None:
        theme = load_theme("minimal")
        assert theme["--sym-pin-input"] == theme["--sym-pin-output"]

    def test_load_print(self) -> None:
        theme = load_theme("print")
        assert theme["--sym-pin-input"] == "#000000"

    def test_all_themes_complete(self) -> None:
        required_keys = set(THEME_DEFAULT.keys())
        for name, theme in BUILTIN_THEMES.items():
            missing = required_keys - set(theme.keys())
            assert not missing, f"Theme '{name}' missing keys: {missing}"

    def test_no_none_values(self) -> None:
        for name, theme in BUILTIN_THEMES.items():
            for key, value in theme.items():
                assert value is not None, (
                    f"Theme '{name}' has None for {key}"
                )


class TestCustomThemeFromFile:
    def test_toml_theme(self) -> None:
        content = '"--sym-bg" = "#000000"\n'
        with tempfile.NamedTemporaryFile(
            suffix=".toml", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            f.flush()
            theme = load_theme(f.name)
        assert theme["--sym-bg"] == "#000000"
        # Other keys should fall back to default
        assert theme["--sym-border"] == THEME_DEFAULT["--sym-border"]

    def test_partial_override_merges(self) -> None:
        content = '"--sym-bg" = "#123456"\n'
        with tempfile.NamedTemporaryFile(
            suffix=".toml", mode="w", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            f.flush()
            theme = load_theme(f.name)
        # Custom value
        assert theme["--sym-bg"] == "#123456"
        # All default keys still present
        for key in THEME_DEFAULT:
            assert key in theme


class TestUnknownTheme:
    def test_unknown_name_returns_default(self) -> None:
        theme = load_theme("nonexistent")
        assert theme == THEME_DEFAULT

    def test_returns_copy_not_reference(self) -> None:
        theme = load_theme("default")
        theme["--sym-bg"] = "modified"
        fresh = load_theme("default")
        assert fresh["--sym-bg"] == "#ffffff"
