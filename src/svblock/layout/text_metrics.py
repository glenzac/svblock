"""Text width measurement for SVG layout sizing."""

from __future__ import annotations

# Pre-computed average character widths at a reference font size of 1.0.
# Monospace: all characters have equal width.
# Proportional: approximation based on common sans-serif fonts (Helvetica/Arial).

_MONOSPACE_CHAR_WIDTH = 0.6  # em-units per character at font-size 1.0

# Proportional widths for ASCII 32-126, normalized to font-size 1.0.
# Based on Helvetica/Arial average glyph widths.
_PROPORTIONAL_WIDTHS: dict[str, float] = {}

# Narrow characters
for c in "iIl|!.,;:'1":
    _PROPORTIONAL_WIDTHS[c] = 0.28
# Medium-narrow
for c in "fjrt()-/[]{}":
    _PROPORTIONAL_WIDTHS[c] = 0.35
# Medium characters (most lowercase and digits)
for c in "abcdeghknopqsuvxyz023456789":
    _PROPORTIONAL_WIDTHS[c] = 0.52
# Medium-wide
for c in "ABCDEFGHKLNPRSTUVXYZ_=+<>?\"#$%&@^~":
    _PROPORTIONAL_WIDTHS[c] = 0.62
# Wide characters
for c in "mwMW":
    _PROPORTIONAL_WIDTHS[c] = 0.74
# Space
_PROPORTIONAL_WIDTHS[" "] = 0.28

_PROPORTIONAL_DEFAULT = 0.52  # fallback for unmapped characters


def measure_text(
    text: str,
    font_size: float,
    font_family: str = "monospace",
) -> float:
    """Measure the rendered width of a text string in SVG user units.

    Args:
        text: The string to measure.
        font_size: Font size in SVG user units (pixels).
        font_family: Either "monospace" or "proportional".

    Returns:
        Estimated width in SVG user units.
    """
    if not text:
        return 0.0

    if font_family == "monospace":
        return len(text) * _MONOSPACE_CHAR_WIDTH * font_size

    # Proportional
    total = sum(
        _PROPORTIONAL_WIDTHS.get(c, _PROPORTIONAL_DEFAULT)
        for c in text
    )
    return total * font_size
