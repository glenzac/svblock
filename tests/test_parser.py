"""Tests for the pyslang-based SystemVerilog parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from svblock.model import PortDirection
from svblock.parser import ParseError, extract_module, extract_modules


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


class TestSimpleModule:
    def test_extract_single_module(self, fixtures_dir: Path) -> None:
        modules = extract_modules(fixtures_dir / "simple_module.sv")
        assert len(modules) == 1
        m = modules[0]
        assert m.name == "simple"
        assert len(m.ports) == 3

    def test_port_directions(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "simple_module.sv")[0]
        clk = m.ports[0]
        assert clk.name == "clk"
        assert clk.direction == PortDirection.INPUT

        rst = m.ports[1]
        assert rst.name == "rst_n"
        assert rst.direction == PortDirection.INPUT

        dout = m.ports[2]
        assert dout.name == "data_out"
        assert dout.direction == PortDirection.OUTPUT

    def test_clock_marker(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "simple_module.sv")[0]
        assert m.ports[0].has_clock_marker is True  # clk
        assert m.ports[1].has_clock_marker is False  # rst_n
        assert m.ports[2].has_clock_marker is False  # data_out

    def test_active_low_marker(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "simple_module.sv")[0]
        assert m.ports[0].has_active_low_marker is False  # clk
        assert m.ports[1].has_active_low_marker is True  # rst_n
        assert m.ports[2].has_active_low_marker is False  # data_out

    def test_scalar_ports_not_bus(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "simple_module.sv")[0]
        for port in m.ports:
            assert port.is_bus is False
            assert port.bus_range is None


class TestBusPorts:
    def test_bus_detection(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "bus_ports.sv")[0]
        data_in = m.ports[0]
        assert data_in.name == "data_in"
        assert data_in.is_bus is True

    def test_parametric_range_as_strings(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "bus_ports.sv")[0]
        data_in = m.ports[0]
        assert data_in.bus_range is not None
        left, right = data_in.bus_range
        # Parametric range should be preserved as text
        assert "WIDTH" in left or left.isdigit()
        assert right == "0"

    def test_literal_range(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "bus_ports.sv")[0]
        nibble = m.ports[2]
        assert nibble.name == "nibble"
        assert nibble.is_bus is True
        assert nibble.bus_range == ("3", "0")

    def test_multidim_array(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "bus_ports.sv")[0]
        matrix = m.ports[3]
        assert matrix.name == "matrix"
        assert matrix.is_bus is True
        # Multi-dim type should contain both dimensions
        assert "[3:0]" in matrix.port_type
        assert "[7:0]" in matrix.port_type


class TestParams:
    def test_param_count(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "params.sv")[0]
        assert len(m.params) == 4

    def test_int_param(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "params.sv")[0]
        width = m.params[0]
        assert width.name == "WIDTH"
        assert width.param_type == "int"
        assert width.default_value == "8"
        assert width.is_localparam is False

    def test_type_param(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "params.sv")[0]
        t = m.params[1]
        assert t.name == "T"
        assert t.param_type == "type"

    def test_string_param(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "params.sv")[0]
        name = m.params[2]
        assert name.name == "NAME"
        assert name.param_type == "string"

    def test_localparam(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "params.sv")[0]
        depth = m.params[3]
        assert depth.name == "DEPTH"
        assert depth.is_localparam is True


class TestInterfacePorts:
    def test_interface_detection(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "interface_ports.sv")[0]
        assert m.name == "iface_mod"
        # clk is a regular port, axi_m and axi_s are interface ports
        iface_ports = [p for p in m.ports if p.is_interface]
        assert len(iface_ports) == 2

    def test_interface_port_details(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "interface_ports.sv")[0]
        axi_m = next(p for p in m.ports if p.name == "axi_m")
        assert axi_m.is_interface is True
        assert axi_m.direction == PortDirection.INTERFACE
        assert axi_m.port_type == "axi_if"
        assert axi_m.modport == "master"

        axi_s = next(p for p in m.ports if p.name == "axi_s")
        assert axi_s.modport == "slave"


class TestMultiModule:
    def test_extracts_all_modules(self, fixtures_dir: Path) -> None:
        modules = extract_modules(fixtures_dir / "multi_module.sv")
        assert len(modules) == 2
        names = {m.name for m in modules}
        assert names == {"mod_a", "mod_b"}

    def test_extract_specific_module(self, fixtures_dir: Path) -> None:
        m = extract_module(fixtures_dir / "multi_module.sv", "mod_b")
        assert m.name == "mod_b"
        assert len(m.ports) == 3

    def test_extract_nonexistent_module(self, fixtures_dir: Path) -> None:
        with pytest.raises(ParseError, match="not found"):
            extract_module(fixtures_dir / "multi_module.sv", "mod_c")


class TestNonAnsi:
    def test_non_ansi_ports(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "non_ansi.sv")[0]
        assert m.name == "non_ansi"
        assert len(m.ports) == 3

    def test_non_ansi_directions(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "non_ansi.sv")[0]
        clk = next(p for p in m.ports if p.name == "clk")
        assert clk.direction == PortDirection.INPUT

        din = next(p for p in m.ports if p.name == "data_in")
        assert din.direction == PortDirection.INPUT
        assert din.is_bus is True

        dout = next(p for p in m.ports if p.name == "data_out")
        assert dout.direction == PortDirection.OUTPUT
        assert dout.is_bus is True


class TestErrorHandling:
    def test_file_not_found(self) -> None:
        with pytest.raises(ParseError, match="File not found"):
            extract_modules("nonexistent.sv")

    def test_file_path_in_module(self, fixtures_dir: Path) -> None:
        m = extract_modules(fixtures_dir / "simple_module.sv")[0]
        assert "simple_module.sv" in m.file_path
