"""PNG export via cairosvg."""

from __future__ import annotations

from pathlib import Path


def svg_to_png(
    svg_content: str,
    output_path: str | Path,
    scale: float = 2.0,
) -> None:
    """Convert SVG string to a PNG file.

    Args:
        svg_content: SVG markup string.
        output_path: Destination path for the PNG file.
        scale: Resolution multiplier (default 2x for retina).

    Raises:
        ImportError: If cairosvg is not installed.
    """
    try:
        import cairosvg
    except ImportError as exc:
        raise ImportError(
            "PNG export requires cairosvg. "
            "Install with: pip install svblock[png]"
        ) from exc

    cairosvg.svg2png(
        bytestring=svg_content.encode("utf-8"),
        write_to=str(output_path),
        scale=scale,
    )
