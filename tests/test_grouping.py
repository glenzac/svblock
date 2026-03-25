"""Tests for heuristic port grouping."""

from __future__ import annotations

from svblock.layout.grouping import apply_grouping
from svblock.model import ModuleIR, PortDef, PortDirection


def _make_module(ports: list[PortDef]) -> ModuleIR:
    return ModuleIR(name="test", file_path="test.sv", ports=ports)


class TestHeuristicGrouping:
    def test_clock_detection(self) -> None:
        ports = [
            PortDef(name="clk", direction=PortDirection.INPUT),
            PortDef(name="sys_clk", direction=PortDirection.INPUT),
            PortDef(name="data", direction=PortDirection.INPUT),
        ]
        result = apply_grouping(_make_module(ports))
        clock_group = next(g for g in result.groups if g.name == "Clocks")
        assert "clk" in clock_group.port_names
        assert "sys_clk" in clock_group.port_names
        assert "data" not in clock_group.port_names

    def test_reset_detection(self) -> None:
        ports = [
            PortDef(name="rst_n", direction=PortDirection.INPUT),
            PortDef(name="reset", direction=PortDirection.INPUT),
            PortDef(name="data", direction=PortDirection.INPUT),
        ]
        result = apply_grouping(_make_module(ports))
        reset_group = next(g for g in result.groups if g.name == "Resets")
        assert "rst_n" in reset_group.port_names
        assert "reset" in reset_group.port_names

    def test_input_output_separation(self) -> None:
        ports = [
            PortDef(name="a", direction=PortDirection.INPUT),
            PortDef(name="b", direction=PortDirection.OUTPUT),
        ]
        result = apply_grouping(_make_module(ports))
        in_group = next(g for g in result.groups if g.name == "Inputs")
        out_group = next(g for g in result.groups if g.name == "Outputs")
        assert in_group.port_names == ["a"]
        assert out_group.port_names == ["b"]

    def test_inout_goes_to_outputs(self) -> None:
        ports = [
            PortDef(name="bidi", direction=PortDirection.INOUT),
        ]
        result = apply_grouping(_make_module(ports))
        out_group = next(g for g in result.groups if g.name == "Outputs")
        assert "bidi" in out_group.port_names

    def test_interface_group(self) -> None:
        ports = [
            PortDef(
                name="axi_m",
                direction=PortDirection.INTERFACE,
                is_interface=True,
            ),
        ]
        result = apply_grouping(_make_module(ports))
        iface_group = next(
            g for g in result.groups if g.name == "Interfaces"
        )
        assert "axi_m" in iface_group.port_names

    def test_empty_groups_excluded(self) -> None:
        ports = [
            PortDef(name="clk", direction=PortDirection.INPUT),
            PortDef(name="out", direction=PortDirection.OUTPUT),
        ]
        result = apply_grouping(_make_module(ports))
        group_names = {g.name for g in result.groups}
        assert "Resets" not in group_names
        assert "Interfaces" not in group_names


class TestExplicitGroupPreservation:
    def test_annotated_groups_preserved(self) -> None:
        ports = [
            PortDef(
                name="clk", direction=PortDirection.INPUT, group="Clock"
            ),
            PortDef(name="data", direction=PortDirection.INPUT),
        ]
        result = apply_grouping(_make_module(ports))
        explicit = next(g for g in result.groups if g.name == "Clock")
        assert "clk" in explicit.port_names

    def test_mixed_annotated_and_heuristic(self) -> None:
        ports = [
            PortDef(
                name="clk", direction=PortDirection.INPUT, group="Timing"
            ),
            PortDef(name="data_in", direction=PortDirection.INPUT),
            PortDef(name="data_out", direction=PortDirection.OUTPUT),
        ]
        result = apply_grouping(_make_module(ports))
        # Explicit group
        timing = next(g for g in result.groups if g.name == "Timing")
        assert "clk" in timing.port_names
        # Heuristic groups
        inputs = next(g for g in result.groups if g.name == "Inputs")
        assert "data_in" in inputs.port_names
        outputs = next(g for g in result.groups if g.name == "Outputs")
        assert "data_out" in outputs.port_names

    def test_explicit_groups_come_first(self) -> None:
        ports = [
            PortDef(
                name="clk", direction=PortDirection.INPUT, group="Custom"
            ),
            PortDef(name="a", direction=PortDirection.INPUT),
        ]
        result = apply_grouping(_make_module(ports))
        assert result.groups[0].name == "Custom"


class TestFlatMode:
    def test_flat_single_group(self) -> None:
        ports = [
            PortDef(name="clk", direction=PortDirection.INPUT),
            PortDef(name="rst", direction=PortDirection.INPUT),
            PortDef(name="out", direction=PortDirection.OUTPUT),
        ]
        result = apply_grouping(_make_module(ports), flat=True)
        assert len(result.groups) == 1
        assert result.groups[0].name == "Ports"
        assert len(result.groups[0].port_names) == 3


class TestPurity:
    def test_does_not_mutate_input(self) -> None:
        ports = [PortDef(name="clk", direction=PortDirection.INPUT)]
        original = _make_module(ports)
        result = apply_grouping(original)
        assert original.groups == []
        assert len(result.groups) > 0
        assert result is not original
