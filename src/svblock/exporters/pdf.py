"""PDF export via cairosvg."""

from __future__ import annotations

from pathlib import Path


def svg_to_pdf(
    svg_content: str,
    output_path: str | Path,
) -> None:
    """Convert SVG string to a PDF file.

    Args:
        svg_content: SVG markup string.
        output_path: Destination path for the PDF file.

    Raises:
        ImportError: If cairosvg is not installed.
    """
    try:
        import cairosvg
    except ImportError as exc:
        raise ImportError(
            "PDF export requires cairosvg. "
            "Install with: pip install svblock[pdf]"
        ) from exc

    cairosvg.svg2pdf(
        bytestring=svg_content.encode("utf-8"),
        write_to=str(output_path),
    )
