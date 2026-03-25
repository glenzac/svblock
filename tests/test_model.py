"""Tests for the svblock data model."""

from __future__ import annotations

from dataclasses import asdict

import pytest

from svblock.model import GroupDef, ModuleIR, ParamDef, PortDef, PortDirection


class TestPortDirection:
    def test_all_members_exist(self) -> None:
        assert PortDirection.INPUT.value == "input"
        assert PortDirection.OUTPUT.value == "output"
        assert PortDirection.INOUT.value == "inout"
        assert PortDirection.INTERFACE.value == "interface"
        assert PortDirection.REF.value == "ref"

    def test_member_count(self) -> None:
        assert len(PortDirection) == 5


class TestPortDef:
    def test_minimal_construction(self) -> None:
        port = PortDef(name="clk", direction=PortDirection.INPUT)
        assert port.name == "clk"
        assert port.direction == PortDirection.INPUT
        assert port.port_type == "logic"
        assert port.is_bus is False
        assert port.bus_range is None
        assert port.is_interface is False
        assert port.modport is None
        assert port.group is None
        assert port.has_clock_marker is False
        assert port.has_active_low_marker is False

    def test_bus_port(self) -> None:
        port = PortDef(
            name="data",
            direction=PortDirection.INPUT,
            port_type="logic [WIDTH-1:0]",
            is_bus=True,
            bus_range=("WIDTH-1", "0"),
        )
        assert port.is_bus is True
        assert port.bus_range == ("WIDTH-1", "0")

    def test_interface_port(self) -> None:
        port = PortDef(
            name="axi_m",
            direction=PortDirection.INTERFACE,
            port_type="axi_if",
            is_interface=True,
            modport="master",
        )
        assert port.is_interface is True
        assert port.modport == "master"

    def test_serialization(self) -> None:
        port = PortDef(name="rst_n", direction=PortDirection.INPUT)
        d = asdict(port)
        assert d["name"] == "rst_n"
        assert d["direction"] == PortDirection.INPUT

    def test_equality(self) -> None:
        a = PortDef(name="clk", direction=PortDirection.INPUT)
        b = PortDef(name="clk", direction=PortDirection.INPUT)
        assert a == b

    def test_inequality(self) -> None:
        a = PortDef(name="clk", direction=PortDirection.INPUT)
        b = PortDef(name="clk", direction=PortDirection.OUTPUT)
        assert a != b


class TestParamDef:
    def test_minimal_construction(self) -> None:
        param = ParamDef(name="WIDTH")
        assert param.name == "WIDTH"
        assert param.param_type == "integer"
        assert param.default_value is None
        assert param.is_localparam is False

    def test_full_construction(self) -> None:
        param = ParamDef(
            name="DEPTH",
            param_type="int",
            default_value="16",
            is_localparam=True,
        )
        assert param.default_value == "16"
        assert param.is_localparam is True

    def test_serialization(self) -> None:
        param = ParamDef(name="W", default_value="8")
        d = asdict(param)
        assert d["name"] == "W"
        assert d["default_value"] == "8"

    def test_equality(self) -> None:
        a = ParamDef(name="W", default_value="8")
        b = ParamDef(name="W", default_value="8")
        assert a == b


class TestGroupDef:
    def test_minimal_construction(self) -> None:
        group = GroupDef(name="Clocks")
        assert group.name == "Clocks"
        assert group.label is None
        assert group.port_names == []

    def test_with_ports(self) -> None:
        group = GroupDef(
            name="Data In",
            label="Input Data",
            port_names=["data_in", "valid_in"],
        )
        assert group.label == "Input Data"
        assert group.port_names == ["data_in", "valid_in"]

    def test_independent_default_lists(self) -> None:
        a = GroupDef(name="A")
        b = GroupDef(name="B")
        a.port_names.append("clk")
        assert b.port_names == []


class TestModuleIR:
    def test_minimal_construction(self) -> None:
        module = ModuleIR(name="top", file_path="top.sv")
        assert module.name == "top"
        assert module.file_path == "top.sv"
        assert module.ports == []
        assert module.params == []
        assert module.groups == []

    def test_with_ports_and_params(self) -> None:
        ports = [
            PortDef(name="clk", direction=PortDirection.INPUT),
            PortDef(name="data_out", direction=PortDirection.OUTPUT, is_bus=True,
                    bus_range=("7", "0")),
            PortDef(name="axi", direction=PortDirection.INTERFACE,
                    is_interface=True, modport="master"),
        ]
        params = [
            ParamDef(name="WIDTH", default_value="8"),
        ]
        groups = [
            GroupDef(name="Clocks", port_names=["clk"]),
            GroupDef(name="Data", port_names=["data_out"]),
            GroupDef(name="Interfaces", port_names=["axi"]),
        ]
        module = ModuleIR(
            name="my_dut",
            file_path="my_dut.sv",
            ports=ports,
            params=params,
            groups=groups,
        )
        assert len(module.ports) == 3
        assert len(module.params) == 1
        assert len(module.groups) == 3

    def test_duplicate_port_name_raises(self) -> None:
        ports = [
            PortDef(name="clk", direction=PortDirection.INPUT),
            PortDef(name="clk", direction=PortDirection.INPUT),
        ]
        with pytest.raises(ValueError, match="Duplicate port name: 'clk'"):
            ModuleIR(name="bad", file_path="bad.sv", ports=ports)

    def test_serialization(self) -> None:
        module = ModuleIR(
            name="top",
            file_path="top.sv",
            ports=[PortDef(name="clk", direction=PortDirection.INPUT)],
        )
        d = asdict(module)
        assert d["name"] == "top"
        assert len(d["ports"]) == 1
        assert d["ports"][0]["name"] == "clk"

    def test_equality(self) -> None:
        a = ModuleIR(name="top", file_path="top.sv")
        b = ModuleIR(name="top", file_path="top.sv")
        assert a == b
