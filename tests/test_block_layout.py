"""Tests for block diagram layout engine."""

from __future__ import annotations

from svblock.layout.block_layout import (
    BlockLayoutConfig,
    compute_block_layout,
)
from svblock.model import (
    BlockDiagramIR,
    ConnectionDef,
    InstanceDef,
    PortDirection,
)


def _simple_ir() -> BlockDiagramIR:
    """Build a simple 3-instance IR: a -> c, b -> c."""
    return BlockDiagramIR(
        parent_name="top",
        file_path="test.sv",
        instances=[
            InstanceDef("u_a", "mod_a"),
            InstanceDef("u_b", "mod_b"),
            InstanceDef("u_c", "mod_c"),
        ],
        connections=[
            ConnectionDef("u_a", "u_c", is_bidirectional=False),
            ConnectionDef("u_b", "u_c", is_bidirectional=False),
        ],
    )


class TestBlockLayout:
    def test_layout_has_all_instances(self) -> None:
        layout = compute_block_layout(_simple_ir())
        names = {b.instance_name for b in layout.instance_boxes}
        assert names == {"u_a", "u_b", "u_c"}

    def test_layout_has_arrows(self) -> None:
        layout = compute_block_layout(_simple_ir())
        assert len(layout.arrows) == 2

    def test_arrows_not_bidirectional(self) -> None:
        layout = compute_block_layout(_simple_ir())
        for arrow in layout.arrows:
            assert arrow.bidirectional is False

    def test_source_boxes_left_of_sink(self) -> None:
        layout = compute_block_layout(_simple_ir())
        box_map = {b.instance_name: b for b in layout.instance_boxes}
        assert box_map["u_a"].x < box_map["u_c"].x
        assert box_map["u_b"].x < box_map["u_c"].x

    def test_parent_boundary_encloses_children(self) -> None:
        layout = compute_block_layout(_simple_ir())
        for box in layout.instance_boxes:
            assert box.x >= layout.parent_x
            assert box.y >= layout.parent_y
            assert box.x + box.width <= layout.parent_x + layout.parent_width
            assert box.y + box.height <= layout.parent_y + layout.parent_height

    def test_parent_name(self) -> None:
        layout = compute_block_layout(_simple_ir())
        assert layout.parent_name == "top"

    def test_total_dimensions_positive(self) -> None:
        layout = compute_block_layout(_simple_ir())
        assert layout.total_width > 0
        assert layout.total_height > 0


class TestBlockLayoutBidir:
    def test_bidirectional_arrow(self) -> None:
        ir = BlockDiagramIR(
            parent_name="top",
            file_path="test.sv",
            instances=[
                InstanceDef("u_a", "mod_a"),
                InstanceDef("u_b", "mod_b"),
            ],
            connections=[
                ConnectionDef("u_a", "u_b", is_bidirectional=True),
            ],
        )
        layout = compute_block_layout(ir)
        assert len(layout.arrows) == 1
        assert layout.arrows[0].bidirectional is True


class TestBlockLayoutEmpty:
    def test_no_instances(self) -> None:
        ir = BlockDiagramIR(parent_name="empty", file_path="test.sv")
        layout = compute_block_layout(ir)
        assert len(layout.instance_boxes) == 0
        assert len(layout.arrows) == 0
        assert layout.total_width > 0
        assert layout.total_height > 0


class TestBlockLayoutParentPorts:
    def test_parent_port_stubs_enabled(self) -> None:
        ir = BlockDiagramIR(
            parent_name="top",
            file_path="test.sv",
            instances=[InstanceDef("u_a", "mod_a")],
            parent_port_instances={"clk": ["u_a"], "y": ["u_a"]},
            parent_port_directions={
                "clk": PortDirection.INPUT,
                "y": PortDirection.OUTPUT,
            },
        )
        config = BlockLayoutConfig(show_parent_ports=True)
        layout = compute_block_layout(ir, config)
        assert len(layout.parent_port_stubs) == 2
        assert layout.show_parent_ports is True

    def test_parent_port_stubs_disabled_by_default(self) -> None:
        ir = BlockDiagramIR(
            parent_name="top",
            file_path="test.sv",
            instances=[InstanceDef("u_a", "mod_a")],
            parent_port_instances={"clk": ["u_a"]},
            parent_port_directions={"clk": PortDirection.INPUT},
        )
        layout = compute_block_layout(ir)
        assert len(layout.parent_port_stubs) == 0
        assert layout.show_parent_ports is False
