"""Built-in themes for svblock SVG output."""

from __future__ import annotations

THEME_DEFAULT: dict[str, str] = {
    "--sym-bg": "#ffffff",
    "--sym-border": "#333333",
    "--sym-text": "#111111",
    "--sym-pin-input": "#1a6db5",
    "--sym-pin-output": "#b52a1a",
    "--sym-pin-inout": "#6a2ab5",
    "--sym-pin-iface": "#1a9e55",
    "--sym-group-bg": "#f0f0f0",
    "--sym-group-text": "#555555",
    "--sym-bus-stroke": "3",
    "--sym-header-bg": "#e8e8e8",
    "--sym-param-text": "#666666",
    "--sym-arrow": "#555555",
    "--sym-instance-bg": "#f8f8f8",
    "--sym-instance-border": "#333333",
    "--sym-parent-border": "#999999",
    "--sym-parent-bg": "#ffffff",
}

THEME_DARK: dict[str, str] = {
    "--sym-bg": "#1e1e2e",
    "--sym-border": "#cdd6f4",
    "--sym-text": "#cdd6f4",
    "--sym-pin-input": "#89b4fa",
    "--sym-pin-output": "#f38ba8",
    "--sym-pin-inout": "#cba6f7",
    "--sym-pin-iface": "#a6e3a1",
    "--sym-group-bg": "#313244",
    "--sym-group-text": "#a6adc8",
    "--sym-bus-stroke": "3",
    "--sym-header-bg": "#313244",
    "--sym-param-text": "#a6adc8",
    "--sym-arrow": "#a6adc8",
    "--sym-instance-bg": "#313244",
    "--sym-instance-border": "#cdd6f4",
    "--sym-parent-border": "#585b70",
    "--sym-parent-bg": "#1e1e2e",
}

THEME_MINIMAL: dict[str, str] = {
    "--sym-bg": "#ffffff",
    "--sym-border": "#444444",
    "--sym-text": "#222222",
    "--sym-pin-input": "#444444",
    "--sym-pin-output": "#444444",
    "--sym-pin-inout": "#444444",
    "--sym-pin-iface": "#444444",
    "--sym-group-bg": "#f5f5f5",
    "--sym-group-text": "#666666",
    "--sym-bus-stroke": "3",
    "--sym-header-bg": "#eeeeee",
    "--sym-param-text": "#666666",
    "--sym-arrow": "#444444",
    "--sym-instance-bg": "#f5f5f5",
    "--sym-instance-border": "#444444",
    "--sym-parent-border": "#888888",
    "--sym-parent-bg": "#ffffff",
}

THEME_PRINT: dict[str, str] = {
    "--sym-bg": "#ffffff",
    "--sym-border": "#000000",
    "--sym-text": "#000000",
    "--sym-pin-input": "#000000",
    "--sym-pin-output": "#000000",
    "--sym-pin-inout": "#000000",
    "--sym-pin-iface": "#000000",
    "--sym-group-bg": "#ffffff",
    "--sym-group-text": "#000000",
    "--sym-bus-stroke": "3",
    "--sym-header-bg": "#e0e0e0",
    "--sym-param-text": "#000000",
    "--sym-arrow": "#000000",
    "--sym-instance-bg": "#ffffff",
    "--sym-instance-border": "#000000",
    "--sym-parent-border": "#000000",
    "--sym-parent-bg": "#ffffff",
}

BUILTIN_THEMES: dict[str, dict[str, str]] = {
    "default": THEME_DEFAULT,
    "dark": THEME_DARK,
    "minimal": THEME_MINIMAL,
    "print": THEME_PRINT,
}
