"""Tests for the @sym comment annotation parser."""

from __future__ import annotations

from pathlib import Path

from svblock.parser import extract_modules
from svblock.parser.annotation import parse_annotations_from_text


class TestAnnotationParsing:
    def test_basic_group_annotation(self) -> None:
        text = '// @sym group="Clocks"\ninput logic clk,\n'
        port_lines = {"clk": 2}
        result = parse_annotations_from_text(text, port_lines)
        assert result["clk"]["group"] == "Clocks"

    def test_unquoted_value(self) -> None:
        text = "// @sym group=Clocks\ninput logic clk,\n"
        port_lines = {"clk": 2}
        result = parse_annotations_from_text(text, port_lines)
        assert result["clk"]["group"] == "Clocks"

    def test_multiple_keys(self) -> None:
        text = '// @sym group="Out" label="Result"\noutput logic data,\n'
        port_lines = {"data": 2}
        result = parse_annotations_from_text(text, port_lines)
        assert result["data"]["group"] == "Out"
        assert result["data"]["label"] == "Result"

    def test_group_propagation(self) -> None:
        text = (
            '// @sym group="Clocks"\n'
            "input logic clk,\n"
            "input logic rst_n,\n"
        )
        port_lines = {"clk": 2, "rst_n": 3}
        result = parse_annotations_from_text(text, port_lines)
        assert result["clk"]["group"] == "Clocks"
        assert result["rst_n"]["group"] == "Clocks"

    def test_blank_line_stops_propagation(self) -> None:
        text = (
            '// @sym group="Clocks"\n'
            "input logic clk,\n"
            "\n"
            "input logic data_in,\n"
        )
        port_lines = {"clk": 2, "data_in": 4}
        result = parse_annotations_from_text(text, port_lines)
        assert "clk" in result
        assert "data_in" not in result

    def test_next_annotation_stops_propagation(self) -> None:
        text = (
            '// @sym group="A"\n'
            "input logic a,\n"
            '// @sym group="B"\n'
            "input logic b,\n"
        )
        port_lines = {"a": 2, "b": 4}
        result = parse_annotations_from_text(text, port_lines)
        assert result["a"]["group"] == "A"
        assert result["b"]["group"] == "B"

    def test_no_annotations_returns_empty(self) -> None:
        text = "input logic clk,\ninput logic rst_n,\n"
        port_lines = {"clk": 1, "rst_n": 2}
        result = parse_annotations_from_text(text, port_lines)
        assert result == {}

    def test_hide_annotation(self) -> None:
        text = "// @sym hide=true\noutput logic debug,\n"
        port_lines = {"debug": 2}
        result = parse_annotations_from_text(text, port_lines)
        assert result["debug"]["hide"] == "true"

    def test_color_annotation(self) -> None:
        text = '// @sym color="#ff0000"\ninput logic err,\n'
        port_lines = {"err": 2}
        result = parse_annotations_from_text(text, port_lines)
        # color value with # won't match unquoted pattern
        # but will match quoted pattern
        assert "err" in result


class TestAnnotatedModuleIntegration:
    def test_annotated_module_groups(self) -> None:
        fixtures = Path(__file__).parent / "fixtures"
        modules = extract_modules(fixtures / "annotated_module.sv")
        m = modules[0]

        clk = next(p for p in m.ports if p.name == "clk")
        assert clk.group == "Clocks"

        rst = next(p for p in m.ports if p.name == "rst_n")
        assert rst.group == "Clocks"

        din = next(p for p in m.ports if p.name == "data_in")
        assert din.group == "Data In"

        vin = next(p for p in m.ports if p.name == "valid_in")
        assert vin.group == "Data In"

        dout = next(p for p in m.ports if p.name == "data_out")
        assert dout.group == "Data Out"

    def test_hidden_port_excluded(self) -> None:
        fixtures = Path(__file__).parent / "fixtures"
        modules = extract_modules(fixtures / "annotated_module.sv")
        m = modules[0]
        port_names = {p.name for p in m.ports}
        assert "debug_out" not in port_names

    def test_port_count_after_hide(self) -> None:
        fixtures = Path(__file__).parent / "fixtures"
        modules = extract_modules(fixtures / "annotated_module.sv")
        m = modules[0]
        # 7 ports declared, 1 hidden = 6 visible
        assert len(m.ports) == 6


class TestPartialAnnotations:
    def test_partial_groups(self) -> None:
        fixtures = Path(__file__).parent / "fixtures"
        m = extract_modules(fixtures / "partial_annotations.sv")[0]

        clk = next(p for p in m.ports if p.name == "clk")
        assert clk.group == "Clocks"

        # data_in and enable have no annotation (blank line separates)
        din = next(p for p in m.ports if p.name == "data_in")
        assert din.group is None

        enable = next(p for p in m.ports if p.name == "enable")
        assert enable.group is None

        dout = next(p for p in m.ports if p.name == "data_out")
        assert dout.group == "Output"
