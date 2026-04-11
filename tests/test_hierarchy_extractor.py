"""Tests for hierarchy extraction (block diagram IR)."""

from __future__ import annotations

from pathlib import Path

import pytest

from svblock.model import PortDirection
from svblock.parser import ParseError, extract_block_diagram


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


class TestBlockSimple:
    """Tests using block_simple.sv: top -> u_a, u_b, u_c."""

    def test_parent_name(self, fixtures_dir: Path) -> None:
        ir = extract_block_diagram(fixtures_dir / "block_simple.sv", "top")
        assert ir.parent_name == "top"

    def test_instances_found(self, fixtures_dir: Path) -> None:
        ir = extract_block_diagram(fixtures_dir / "block_simple.sv", "top")
        names = [(i.instance_name, i.module_name) for i in ir.instances]
        assert ("u_a", "mod_a") in names
        assert ("u_b", "mod_b") in names
        assert ("u_c", "mod_c") in names
        assert len(ir.instances) == 3

    def test_connections_unidirectional(self, fixtures_dir: Path) -> None:
        ir = extract_block_diagram(fixtures_dir / "block_simple.sv", "top")
        conn_set = {
            (c.from_instance, c.to_instance, c.is_bidirectional)
            for c in ir.connections
        }
        assert ("u_a", "u_c", False) in conn_set
        assert ("u_b", "u_c", False) in conn_set

    def test_no_a_b_connection(self, fixtures_dir: Path) -> None:
        ir = extract_block_diagram(fixtures_dir / "block_simple.sv", "top")
        pairs = {frozenset([c.from_instance, c.to_instance]) for c in ir.connections}
        assert frozenset(["u_a", "u_b"]) not in pairs

    def test_parent_ports(self, fixtures_dir: Path) -> None:
        ir = extract_block_diagram(fixtures_dir / "block_simple.sv", "top")
        assert "clk" in ir.parent_port_instances
        assert "x" in ir.parent_port_instances
        assert "y" in ir.parent_port_instances

    def test_parent_port_directions(self, fixtures_dir: Path) -> None:
        ir = extract_block_diagram(fixtures_dir / "block_simple.sv", "top")
        assert ir.parent_port_directions["clk"] == PortDirection.INPUT
        assert ir.parent_port_directions["x"] == PortDirection.INPUT
        assert ir.parent_port_directions["y"] == PortDirection.OUTPUT


class TestBlockBidir:
    """Tests using block_bidir.sv: bidirectional connections."""

    def test_bidirectional_connection(self, fixtures_dir: Path) -> None:
        ir = extract_block_diagram(fixtures_dir / "block_bidir.sv", "top_bidir")
        assert len(ir.connections) == 1
        conn = ir.connections[0]
        assert conn.is_bidirectional is True
        assert frozenset([conn.from_instance, conn.to_instance]) == frozenset(
            ["u_a", "u_b"]
        )


class TestBlockSingle:
    """Tests using block_single.sv: single instance."""

    def test_single_instance(self, fixtures_dir: Path) -> None:
        ir = extract_block_diagram(fixtures_dir / "block_single.sv", "wrapper")
        assert len(ir.instances) == 1
        assert ir.instances[0].instance_name == "u0"
        assert ir.instances[0].module_name == "inner"

    def test_no_internal_connections(self, fixtures_dir: Path) -> None:
        ir = extract_block_diagram(fixtures_dir / "block_single.sv", "wrapper")
        assert len(ir.connections) == 0


class TestBlockEdgeCases:
    """Edge cases and error handling."""

    def test_module_not_found(self, fixtures_dir: Path) -> None:
        with pytest.raises(ParseError, match="not found"):
            extract_block_diagram(fixtures_dir / "block_simple.sv", "nonexistent")

    def test_file_not_found(self) -> None:
        with pytest.raises(ParseError, match="File not found"):
            extract_block_diagram("/nonexistent/path.sv")

    def test_module_with_no_instances(self, fixtures_dir: Path) -> None:
        # simple_module.sv defines a module with no sub-instances
        ir = extract_block_diagram(fixtures_dir / "simple_module.sv", "simple")
        assert len(ir.instances) == 0
        assert len(ir.connections) == 0

    def test_default_module_selection(self, fixtures_dir: Path) -> None:
        ir = extract_block_diagram(fixtures_dir / "block_single.sv")
        assert ir.parent_name == "wrapper"
