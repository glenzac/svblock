"""Tests for the SVG renderer."""

from __future__ import annotations

import xml.etree.ElementTree as ET

from svblock.layout.engine import (
    DecoratorType,
    GroupSeparator,
    HeaderRect,
    LayoutSpec,
    PinRow,
    PinSide,
)
from svblock.renderer.svg_renderer import (
    RenderOptions,
    render_svg,
)


def _make_layout(
    pin_rows: list[PinRow] | None = None,
    group_separators: list[GroupSeparator] | None = None,
    params_text: list[str] | None = None,
) -> LayoutSpec:
    return LayoutSpec(
        box_x=30.0,
        box_y=0.0,
        box_width=240.0,
        box_height=120.0,
        header_rect=HeaderRect(x=30.0, y=0.0, width=240.0, height=36.0),
        module_name="test_mod",
        params_text=params_text or [],
        pin_rows=pin_rows or [],
        group_separators=group_separators or [],
        total_width=300.0,
        total_height=120.0,
    )


class TestSVGValidity:
    def test_parses_as_xml(self) -> None:
        svg = render_svg(_make_layout())
        ET.fromstring(svg)  # should not raise

    def test_has_svg_root(self) -> None:
        svg = render_svg(_make_layout())
        root = ET.fromstring(svg)
        assert root.tag == "{http://www.w3.org/2000/svg}svg"

    def test_has_xmlns(self) -> None:
        svg = render_svg(_make_layout())
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg

    def test_standalone_false_no_xmlns(self) -> None:
        svg = render_svg(
            _make_layout(), options=RenderOptions(standalone=False)
        )
        assert "xmlns" not in svg

    def test_has_svblock_class(self) -> None:
        svg = render_svg(_make_layout())
        assert 'class="svblock"' in svg


class TestDeterminism:
    def test_no_timestamps(self) -> None:
        svg = render_svg(_make_layout())
        assert "timestamp" not in svg.lower()
        assert "date" not in svg.lower()

    def test_deterministic_output(self) -> None:
        layout = _make_layout()
        svg1 = render_svg(layout)
        svg2 = render_svg(layout)
        assert svg1 == svg2

    def test_float_rounding(self) -> None:
        layout = _make_layout()
        layout.box_x = 30.123456
        svg = render_svg(layout)
        assert "30.12" in svg
        assert "30.123456" not in svg


class TestElementIDs:
    def test_module_name_id(self) -> None:
        svg = render_svg(_make_layout())
        assert 'id="module-test_mod"' in svg

    def test_port_id(self) -> None:
        pin = PinRow(
            port_name="clk", side=PinSide.LEFT, y=50.0,
            label_text="clk", decorator=DecoratorType.NONE,
        )
        svg = render_svg(_make_layout(pin_rows=[pin]))
        assert 'id="port-clk"' in svg

    def test_group_id(self) -> None:
        sep = GroupSeparator(y=60.0, label="Clocks")
        svg = render_svg(_make_layout(group_separators=[sep]))
        assert 'id="group-Clocks"' in svg

    def test_param_id(self) -> None:
        svg = render_svg(_make_layout(params_text=["int WIDTH = 8"]))
        assert 'id="param-WIDTH"' in svg


class TestPinRendering:
    def test_left_pin_line(self) -> None:
        pin = PinRow(
            port_name="clk", side=PinSide.LEFT, y=50.0,
            label_text="clk", decorator=DecoratorType.NONE,
        )
        svg = render_svg(_make_layout(pin_rows=[pin]))
        assert "port-clk" in svg
        assert "clk" in svg

    def test_right_pin_line(self) -> None:
        pin = PinRow(
            port_name="out", side=PinSide.RIGHT, y=50.0,
            label_text="out", decorator=DecoratorType.NONE,
        )
        svg = render_svg(_make_layout(pin_rows=[pin]))
        assert "port-out" in svg

    def test_bus_label_shown(self) -> None:
        pin = PinRow(
            port_name="data", side=PinSide.LEFT, y=50.0,
            label_text="data", decorator=DecoratorType.BUS,
            bus_label="[7:0]",
        )
        svg = render_svg(_make_layout(pin_rows=[pin]))
        assert "[7:0]" in svg

    def test_title_element_for_hover(self) -> None:
        pin = PinRow(
            port_name="clk", side=PinSide.LEFT, y=50.0,
            label_text="clk", decorator=DecoratorType.NONE,
        )
        svg = render_svg(_make_layout(pin_rows=[pin]))
        assert "<title>clk</title>" in svg


class TestDecorators:
    def test_clock_triangle(self) -> None:
        pin = PinRow(
            port_name="clk", side=PinSide.LEFT, y=50.0,
            label_text="clk", decorator=DecoratorType.CLOCK,
        )
        svg = render_svg(_make_layout(pin_rows=[pin]))
        assert "<polygon" in svg

    def test_active_low_bubble(self) -> None:
        pin = PinRow(
            port_name="rst_n", side=PinSide.LEFT, y=50.0,
            label_text="rst_n", decorator=DecoratorType.ACTIVE_LOW,
        )
        svg = render_svg(_make_layout(pin_rows=[pin]))
        assert "<circle" in svg

    def test_interface_diamond(self) -> None:
        pin = PinRow(
            port_name="axi", side=PinSide.RIGHT, y=50.0,
            label_text="axi", decorator=DecoratorType.INTERFACE,
        )
        svg = render_svg(_make_layout(pin_rows=[pin]))
        assert "<polygon" in svg

    def test_inout_arrow(self) -> None:
        pin = PinRow(
            port_name="bidi", side=PinSide.RIGHT, y=50.0,
            label_text="bidi", decorator=DecoratorType.INOUT,
        )
        svg = render_svg(_make_layout(pin_rows=[pin]))
        assert "<path" in svg

    def test_no_decorators_option(self) -> None:
        pin = PinRow(
            port_name="clk", side=PinSide.LEFT, y=50.0,
            label_text="clk", decorator=DecoratorType.CLOCK,
        )
        svg = render_svg(
            _make_layout(pin_rows=[pin]),
            options=RenderOptions(no_decorators=True),
        )
        assert "<polygon" not in svg


class TestTheming:
    def test_default_theme_injected(self) -> None:
        svg = render_svg(_make_layout())
        assert "--sym-bg" in svg
        assert "#ffffff" in svg

    def test_custom_theme_override(self) -> None:
        theme = {"--sym-bg": "#000000"}
        svg = render_svg(_make_layout(), theme=theme)
        assert "#000000" in svg

    def test_custom_theme_merges(self) -> None:
        theme = {"--sym-bg": "#000000"}
        svg = render_svg(_make_layout(), theme=theme)
        # Should still have other default vars
        assert "--sym-border" in svg
