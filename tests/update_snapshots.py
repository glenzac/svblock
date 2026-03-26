#!/usr/bin/env python3
"""Regenerate golden SVG snapshots from test fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from svblock.config import load_theme
from svblock.layout.engine import LayoutConfig, compute_layout
from svblock.layout.grouping import apply_grouping
from svblock.parser import extract_modules
from svblock.renderer.svg_renderer import RenderOptions, render_svg

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"


def generate_snapshot(fixture_name: str) -> None:
    """Render a fixture and write the golden SVG."""
    sv_path = FIXTURES_DIR / f"{fixture_name}.sv"
    if not sv_path.exists():
        print(f"  SKIP {fixture_name} (file not found)")
        return

    modules = extract_modules(sv_path)
    if not modules:
        print(f"  SKIP {fixture_name} (no modules)")
        return

    for module in modules:
        module = apply_grouping(module)
        layout = compute_layout(module, LayoutConfig())
        theme = load_theme("default")
        svg = render_svg(layout, theme, RenderOptions())

        out_name = f"{fixture_name}_{module.name}.svg"
        out_path = SNAPSHOTS_DIR / out_name
        out_path.write_text(svg, encoding="utf-8")
        print(f"  WROTE {out_name}")


FIXTURES = [
    "simple_module",
    "bus_ports",
    "params",
    "interface_ports",
    "multi_module",
    "non_ansi",
    "annotated_module",
    "partial_annotations",
    "clock_reset",
    "active_low",
    "multidim_array",
    "type_params",
    "no_ports",
    "large_module",
    "heuristic_groups",
]


def main() -> None:
    SNAPSHOTS_DIR.mkdir(exist_ok=True)
    print(f"Generating snapshots in {SNAPSHOTS_DIR}")
    for name in FIXTURES:
        generate_snapshot(name)
    print("Done.")


if __name__ == "__main__":
    main()
