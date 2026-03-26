"""Tests for PNG and PDF exporters."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPNGExporter:
    def test_import_error_message(self) -> None:
        """Raise ImportError with install hint when cairosvg missing."""
        with patch.dict(sys.modules, {"cairosvg": None}):
            # Force reimport
            if "svblock.exporters.png" in sys.modules:
                del sys.modules["svblock.exporters.png"]
            from svblock.exporters.png import svg_to_png

            with pytest.raises(ImportError, match="pip install svblock"):
                svg_to_png("<svg></svg>", "out.png")

    def test_calls_cairosvg(self, tmp_path: Path) -> None:
        """Verify cairosvg.svg2png is called with correct args."""
        mock_cairo = MagicMock()
        with patch.dict(sys.modules, {"cairosvg": mock_cairo}):
            if "svblock.exporters.png" in sys.modules:
                del sys.modules["svblock.exporters.png"]
            from svblock.exporters.png import svg_to_png

            out = tmp_path / "test.png"
            svg_to_png("<svg>test</svg>", out, scale=3.0)
            mock_cairo.svg2png.assert_called_once_with(
                bytestring=b"<svg>test</svg>",
                write_to=str(out),
                scale=3.0,
            )

    def test_default_scale(self, tmp_path: Path) -> None:
        """Default scale is 2.0."""
        mock_cairo = MagicMock()
        with patch.dict(sys.modules, {"cairosvg": mock_cairo}):
            if "svblock.exporters.png" in sys.modules:
                del sys.modules["svblock.exporters.png"]
            from svblock.exporters.png import svg_to_png

            svg_to_png("<svg/>", tmp_path / "test.png")
            call_kwargs = mock_cairo.svg2png.call_args[1]
            assert call_kwargs["scale"] == 2.0


class TestPDFExporter:
    def test_import_error_message(self) -> None:
        """Raise ImportError with install hint when cairosvg missing."""
        with patch.dict(sys.modules, {"cairosvg": None}):
            if "svblock.exporters.pdf" in sys.modules:
                del sys.modules["svblock.exporters.pdf"]
            from svblock.exporters.pdf import svg_to_pdf

            with pytest.raises(ImportError, match="pip install svblock"):
                svg_to_pdf("<svg></svg>", "out.pdf")

    def test_calls_cairosvg(self, tmp_path: Path) -> None:
        """Verify cairosvg.svg2pdf is called with correct args."""
        mock_cairo = MagicMock()
        with patch.dict(sys.modules, {"cairosvg": mock_cairo}):
            if "svblock.exporters.pdf" in sys.modules:
                del sys.modules["svblock.exporters.pdf"]
            from svblock.exporters.pdf import svg_to_pdf

            out = tmp_path / "test.pdf"
            svg_to_pdf("<svg>test</svg>", out)
            mock_cairo.svg2pdf.assert_called_once_with(
                bytestring=b"<svg>test</svg>",
                write_to=str(out),
            )
