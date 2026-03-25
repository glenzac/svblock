"""Tests for text width measurement."""

from __future__ import annotations

from svblock.layout.text_metrics import measure_text


class TestMonospace:
    def test_positive_width(self) -> None:
        assert measure_text("clk", 14) > 0

    def test_equal_width_chars(self) -> None:
        w1 = measure_text("iii", 14)
        w2 = measure_text("WWW", 14)
        assert w1 == w2  # monospace: all chars same width

    def test_scales_with_length(self) -> None:
        w1 = measure_text("ab", 14)
        w2 = measure_text("abcd", 14)
        assert w2 == w1 * 2

    def test_scales_with_font_size(self) -> None:
        w1 = measure_text("test", 10)
        w2 = measure_text("test", 20)
        assert w2 == w1 * 2

    def test_empty_string(self) -> None:
        assert measure_text("", 14) == 0.0


class TestProportional:
    def test_positive_width(self) -> None:
        assert measure_text("clk", 14, "proportional") > 0

    def test_w_wider_than_i(self) -> None:
        w_width = measure_text("W", 14, "proportional")
        i_width = measure_text("i", 14, "proportional")
        assert w_width > i_width

    def test_scales_with_font_size(self) -> None:
        w1 = measure_text("test", 10, "proportional")
        w2 = measure_text("test", 20, "proportional")
        assert abs(w2 - w1 * 2) < 0.001

    def test_empty_string(self) -> None:
        assert measure_text("", 14, "proportional") == 0.0


class TestDeterminism:
    def test_same_input_same_output(self) -> None:
        results = [measure_text("data_out", 14) for _ in range(10)]
        assert len(set(results)) == 1
