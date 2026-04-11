"""Tests for block diagram SVG renderer."""

from __future__ import annotations

from svblock.layout.block_layout import (
    Arrow,
    BlockLayoutSpec,
    InstanceBox,
    ParentPortStub,
)
from svblock.model import PortDirection
from svblock.renderer.block_renderer import render_block_svg


def _simple_layout() -> BlockLayoutSpec:
    """A minimal layout with two instances and one arrow."""
    return BlockLayoutSpec(
        parent_name="top",
        parent_x=0,
        parent_y=0,
        parent_width=400,
        parent_height=200,
        instance_boxes=[
            InstanceBox("u_a", "mod_a", x=50, y=75, width=120, height=50),
            InstanceBox("u_b", "mod_b", x=230, y=75, width=120, height=50),
        ],
        arrows=[
            Arrow(from_x=170, from_y=100, to_x=230, to_y=100, bidirectional=False),
        ],
        total_width=400,
        total_height=200,
    )


class TestBlockRendererBasic:
    def test_output_is_valid_svg(self) -> None:
        svg = render_block_svg(_simple_layout())
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")

    def test_contains_xmlns(self) -> None:
        svg = render_block_svg(_simple_layout(), standalone=True)
        assert 'xmlns="http://www.w3.org/2000/svg"' in svg

    def test_no_xmlns_when_not_standalone(self) -> None:
        svg = render_block_svg(_simple_layout(), standalone=False)
        assert "xmlns" not in svg

    def test_contains_parent_label(self) -> None:
        svg = render_block_svg(_simple_layout())
        assert "top" in svg
        assert "svblock-block-parent-label" in svg

    def test_contains_instance_boxes(self) -> None:
        svg = render_block_svg(_simple_layout())
        assert 'id="inst-u_a"' in svg
        assert 'id="inst-u_b"' in svg

    def test_contains_instance_labels(self) -> None:
        svg = render_block_svg(_simple_layout())
        assert "u_a" in svg
        assert "mod_a" in svg
        assert "u_b" in svg
        assert "mod_b" in svg

    def test_contains_arrow_markers(self) -> None:
        svg = render_block_svg(_simple_layout())
        assert 'id="arrow-end"' in svg
        assert "marker-end" in svg

    def test_arrow_not_bidirectional(self) -> None:
        svg = render_block_svg(_simple_layout())
        # Unidirectional arrow lines should not reference marker-start
        arrow_lines = [
            s for s in svg.split("\n")
            if "svblock-block-arrow" in s and "<line" in s
        ]
        for line in arrow_lines:
            assert "marker-start" not in line


class TestBlockRendererBidir:
    def test_bidirectional_arrow(self) -> None:
        layout = BlockLayoutSpec(
            parent_name="top",
            parent_x=0,
            parent_y=0,
            parent_width=400,
            parent_height=200,
            instance_boxes=[
                InstanceBox("u_a", "mod_a", x=50, y=75, width=120, height=50),
                InstanceBox("u_b", "mod_b", x=230, y=75, width=120, height=50),
            ],
            arrows=[
                Arrow(from_x=170, from_y=100, to_x=230, to_y=100, bidirectional=True),
            ],
            total_width=400,
            total_height=200,
        )
        svg = render_block_svg(layout)
        # The line itself should have both marker-start and marker-end
        lines = [
            s for s in svg.split("\n")
            if "svblock-block-arrow" in s and "<line" in s
        ]
        assert len(lines) == 1
        assert "marker-start" in lines[0]
        assert "marker-end" in lines[0]


class TestBlockRendererTheme:
    def test_custom_theme_applied(self) -> None:
        theme = {"--sym-arrow": "#ff0000", "--sym-text": "#00ff00"}
        svg = render_block_svg(_simple_layout(), theme=theme)
        assert "#ff0000" in svg
        assert "#00ff00" in svg

    def test_default_theme_used(self) -> None:
        svg = render_block_svg(_simple_layout())
        assert "--sym-arrow" in svg


class TestBlockRendererPortStubs:
    def test_port_stubs_rendered(self) -> None:
        layout = BlockLayoutSpec(
            parent_name="top",
            parent_x=0,
            parent_y=0,
            parent_width=400,
            parent_height=200,
            instance_boxes=[
                InstanceBox("u_a", "mod_a", x=100, y=75, width=120, height=50),
            ],
            arrows=[],
            parent_port_stubs=[
                ParentPortStub(
                    port_name="clk",
                    direction=PortDirection.INPUT,
                    label_x=-5,
                    label_y=100,
                    line_x1=0,
                    line_y1=100,
                    line_x2=100,
                    line_y2=100,
                ),
            ],
            total_width=400,
            total_height=200,
            show_parent_ports=True,
        )
        svg = render_block_svg(layout)
        assert "clk" in svg
        assert "svblock-block-port-line" in svg
        assert "svblock-block-port-label" in svg
