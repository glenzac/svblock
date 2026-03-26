"""End-to-end tests: parse → group → layout → render, compare to golden SVGs."""

from __future__ import annotations

from pathlib import Path

import pytest

from svblock.config import load_theme
from svblock.layout.engine import LayoutConfig, compute_layout
from svblock.layout.grouping import apply_grouping
from svblock.parser import extract_modules
from svblock.renderer.svg_renderer import RenderOptions, render_svg

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SNAPSHOTS_DIR = Path(__file__).parent / "snapshots"


def _render_fixture(fixture_name: str, module_name: str | None = None) -> str:
    """Run the full pipeline on a fixture and return SVG string."""
    sv_path = FIXTURES_DIR / f"{fixture_name}.sv"
    modules = extract_modules(sv_path)
    if module_name:
        module = next(m for m in modules if m.name == module_name)
    else:
        module = modules[0]
    module = apply_grouping(module)
    layout = compute_layout(module, LayoutConfig())
    theme = load_theme("default")
    return render_svg(layout, theme, RenderOptions())


def _load_snapshot(snapshot_name: str) -> str:
    """Load a golden SVG snapshot."""
    path = SNAPSHOTS_DIR / snapshot_name
    if not path.exists():
        pytest.skip(
            f"Snapshot {snapshot_name} not found. "
            f"Run: python tests/update_snapshots.py"
        )
    return path.read_text(encoding="utf-8")


class TestE2ESimple:
    def test_simple_module(self) -> None:
        svg = _render_fixture("simple_module")
        golden = _load_snapshot("simple_module_simple.svg")
        assert svg == golden

    def test_bus_ports(self) -> None:
        svg = _render_fixture("bus_ports")
        golden = _load_snapshot("bus_ports_bus_mod.svg")
        assert svg == golden

    def test_params(self) -> None:
        svg = _render_fixture("params")
        golden = _load_snapshot("params_param_mod.svg")
        assert svg == golden


class TestE2EAnnotations:
    def test_annotated_module(self) -> None:
        svg = _render_fixture("annotated_module")
        golden = _load_snapshot("annotated_module_annotated.svg")
        assert svg == golden

    def test_partial_annotations(self) -> None:
        svg = _render_fixture("partial_annotations")
        golden = _load_snapshot("partial_annotations_partial.svg")
        assert svg == golden


class TestE2EInterfaces:
    def test_interface_ports(self) -> None:
        svg = _render_fixture("interface_ports")
        golden = _load_snapshot("interface_ports_iface_mod.svg")
        assert svg == golden


class TestE2EMultiModule:
    def test_multi_module_first(self) -> None:
        svg = _render_fixture("multi_module", "mod_a")
        golden = _load_snapshot("multi_module_mod_a.svg")
        assert svg == golden

    def test_multi_module_second(self) -> None:
        svg = _render_fixture("multi_module", "mod_b")
        golden = _load_snapshot("multi_module_mod_b.svg")
        assert svg == golden


class TestE2EDecorators:
    def test_clock_reset(self) -> None:
        svg = _render_fixture("clock_reset")
        golden = _load_snapshot("clock_reset_clock_reset.svg")
        assert svg == golden

    def test_active_low(self) -> None:
        svg = _render_fixture("active_low")
        golden = _load_snapshot("active_low_active_low.svg")
        assert svg == golden


class TestE2EAdvanced:
    def test_multidim_array(self) -> None:
        svg = _render_fixture("multidim_array")
        golden = _load_snapshot("multidim_array_multidim.svg")
        assert svg == golden

    def test_type_params(self) -> None:
        svg = _render_fixture("type_params")
        golden = _load_snapshot("type_params_type_params.svg")
        assert svg == golden

    def test_no_ports(self) -> None:
        svg = _render_fixture("no_ports")
        golden = _load_snapshot("no_ports_no_ports.svg")
        assert svg == golden

    def test_non_ansi(self) -> None:
        svg = _render_fixture("non_ansi")
        golden = _load_snapshot("non_ansi_non_ansi.svg")
        assert svg == golden


class TestE2EGrouping:
    def test_large_module_with_annotations(self) -> None:
        svg = _render_fixture("large_module")
        golden = _load_snapshot("large_module_large_mod.svg")
        assert svg == golden

    def test_heuristic_groups(self) -> None:
        svg = _render_fixture("heuristic_groups")
        golden = _load_snapshot("heuristic_groups_heuristic.svg")
        assert svg == golden


class TestE2EOptions:
    def test_no_decorators(self) -> None:
        """Ensure no-decorators renders without crashing."""
        sv_path = FIXTURES_DIR / "clock_reset.sv"
        modules = extract_modules(sv_path)
        module = apply_grouping(modules[0])
        config = LayoutConfig(no_decorators=True)
        layout = compute_layout(module, config)
        theme = load_theme("default")
        opts = RenderOptions(no_decorators=True)
        svg = render_svg(layout, theme, opts)
        assert "<svg" in svg
        # Should NOT have clock triangle
        assert "polygon" not in svg

    def test_no_params(self) -> None:
        """Ensure no-params suppresses parameter text."""
        sv_path = FIXTURES_DIR / "params.sv"
        modules = extract_modules(sv_path)
        module = apply_grouping(modules[0])
        config = LayoutConfig(no_params=True)
        layout = compute_layout(module, config)
        theme = load_theme("default")
        opts = RenderOptions(no_params=True)
        svg = render_svg(layout, theme, opts)
        assert 'id="param-' not in svg

    def test_no_groups_flat(self) -> None:
        """Ensure flat mode suppresses group separators."""
        sv_path = FIXTURES_DIR / "large_module.sv"
        modules = extract_modules(sv_path)
        module = apply_grouping(modules[0], flat=True)
        config = LayoutConfig(no_groups=True)
        layout = compute_layout(module, config)
        theme = load_theme("default")
        svg = render_svg(layout, theme, RenderOptions())
        assert 'class="svblock-group-sep"' not in svg

    def test_dark_theme(self) -> None:
        """Ensure dark theme CSS variables appear in output."""
        sv_path = FIXTURES_DIR / "simple_module.sv"
        modules = extract_modules(sv_path)
        module = apply_grouping(modules[0])
        layout = compute_layout(module, LayoutConfig())
        theme = load_theme("dark")
        svg = render_svg(layout, theme, RenderOptions())
        assert "#1e1e2e" in svg

    def test_sphinx_mode(self) -> None:
        """Sphinx mode omits xmlns."""
        sv_path = FIXTURES_DIR / "simple_module.sv"
        modules = extract_modules(sv_path)
        module = apply_grouping(modules[0])
        layout = compute_layout(module, LayoutConfig())
        theme = load_theme("default")
        opts = RenderOptions(standalone=False)
        svg = render_svg(layout, theme, opts)
        assert "xmlns" not in svg
