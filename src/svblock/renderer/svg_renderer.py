"""Pure Python SVG renderer for module symbols."""

from __future__ import annotations

from dataclasses import dataclass

from svblock.layout.engine import (
    DecoratorType,
    LayoutSpec,
    PinRow,
    PinSide,
)


@dataclass
class RenderOptions:
    no_decorators: bool = False
    no_params: bool = False
    standalone: bool = True


# Default theme (light)
DEFAULT_THEME: dict[str, str] = {
    "--sym-bg": "#ffffff",
    "--sym-border": "#333333",
    "--sym-text": "#111111",
    "--sym-pin-input": "#1a6db5",
    "--sym-pin-output": "#b52a1a",
    "--sym-pin-inout": "#6a2ab5",
    "--sym-pin-iface": "#1a9e55",
    "--sym-group-bg": "#f0f0f0",
    "--sym-group-text": "#555555",
    "--sym-bus-stroke": "3",
    "--sym-header-bg": "#e8e8e8",
    "--sym-param-text": "#666666",
}


def _fmt(v: float) -> str:
    """Format a float to 2 decimal places, stripping trailing zeros."""
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _css_block(theme: dict[str, str]) -> str:
    """Generate the CSS style block."""
    variables = "\n".join(
        f"      {k}: {v};" for k, v in theme.items()
    )
    # CSS rules as list to avoid long lines in source
    rules = [
        ".svblock-box-fill { fill: var(--sym-bg); stroke: none; }",
        ".svblock-box-border { fill: none; "
        "stroke: var(--sym-border); stroke-width: 1.5; }",
        ".svblock-header { fill: var(--sym-header-bg); }",
        ".svblock-name { font-family: sans-serif; "
        "font-size: 15px; font-weight: bold; "
        "fill: var(--sym-text); }",
        ".svblock-param { font-family: monospace; "
        "font-size: 11px; fill: var(--sym-param-text); }",
        ".svblock-port { font-family: monospace; "
        "font-size: 13px; }",
        ".svblock-port-in { fill: var(--sym-pin-input); }",
        ".svblock-port-out { fill: var(--sym-pin-output); }",
        ".svblock-port-inout { fill: var(--sym-pin-inout); }",
        ".svblock-port-iface { fill: var(--sym-pin-iface); }",
        ".svblock-pin { stroke-width: 1.5; }",
        ".svblock-pin-bus { "
        "stroke-width: var(--sym-bus-stroke); }",
        ".svblock-group-sep { stroke: var(--sym-group-text); "
        "stroke-width: 0.5; stroke-dasharray: 4,2; }",
        ".svblock-group-label { font-family: sans-serif; "
        "font-size: 11px; fill: var(--sym-group-text); "
        "text-anchor: middle; }",
    ]
    css_rules = "\n".join(f"      {r}" for r in rules)
    return (
        "    <style>\n"
        "      :root {\n"
        f"{variables}\n"
        "      }\n"
        f"{css_rules}\n"
        "    </style>"
    )


def _port_css_class(pin: PinRow) -> str:
    """Get the CSS class for a port based on its decorator/side."""
    if pin.decorator == DecoratorType.INTERFACE:
        return "svblock-port-iface"
    if pin.decorator == DecoratorType.INOUT:
        return "svblock-port-inout"
    if pin.side == PinSide.LEFT:
        return "svblock-port-in"
    return "svblock-port-out"


def _pin_stroke_class(pin: PinRow) -> str:
    """Get the stroke class for a pin line."""
    if pin.decorator == DecoratorType.BUS:
        return "svblock-pin-bus"
    return "svblock-pin"


def _clock_triangle(
    x: float, y: float, size: float = 6, flip: bool = False,
) -> str:
    """Small triangle marker for clock pins.

    When flip=False, the triangle points right (for left-side pins).
    When flip=True, the triangle points left (for right-side pins).
    """
    s = size
    if flip:
        return (
            f'<polygon points="{_fmt(x)},{_fmt(y - s)} '
            f'{_fmt(x - s)},{_fmt(y)} '
            f'{_fmt(x)},{_fmt(y + s)}" '
            f'fill="none" stroke="currentColor" stroke-width="1"/>'
        )
    return (
        f'<polygon points="{_fmt(x)},{_fmt(y - s)} '
        f'{_fmt(x + s)},{_fmt(y)} '
        f'{_fmt(x)},{_fmt(y + s)}" '
        f'fill="none" stroke="currentColor" stroke-width="1"/>'
    )


def _inversion_bubble(x: float, y: float, r: float = 3) -> str:
    """Small circle for active-low pins."""
    return (
        f'<circle cx="{_fmt(x)}" cy="{_fmt(y)}" r="{_fmt(r)}" '
        f'fill="var(--sym-bg)" stroke="currentColor" stroke-width="1"/>'
    )


def _interface_diamond(x: float, y: float, size: float = 5) -> str:
    """Filled diamond for interface pins."""
    s = size
    return (
        f'<polygon points="{_fmt(x)},{_fmt(y - s)} '
        f'{_fmt(x + s)},{_fmt(y)} '
        f'{_fmt(x)},{_fmt(y + s)} '
        f'{_fmt(x - s)},{_fmt(y)}" '
        f'fill="currentColor"/>'
    )


def _inout_arrow(x: float, y: float, size: float = 5) -> str:
    """Double-headed arrow for inout pins."""
    s = size
    return (
        f'<path d="M{_fmt(x - s)},{_fmt(y)} L{_fmt(x + s)},{_fmt(y)} '
        f'M{_fmt(x + s - 3)},{_fmt(y - 3)} L{_fmt(x + s)},{_fmt(y)} '
        f'L{_fmt(x + s - 3)},{_fmt(y + 3)} '
        f'M{_fmt(x - s + 3)},{_fmt(y - 3)} L{_fmt(x - s)},{_fmt(y)} '
        f'L{_fmt(x - s + 3)},{_fmt(y + 3)}" '
        f'fill="none" stroke="currentColor" stroke-width="1.5"/>'
    )


def _render_decorator(
    pin: PinRow, x: float, y: float, side: PinSide
) -> str:
    """Render the decorator symbol for a pin."""
    # Border half-width offset so decorators sit flush against the visible
    # inner edge of the module boundary (stroke-width 1.5 → offset 0.75).
    border_offset = 0.75
    if pin.decorator == DecoratorType.CLOCK:
        if side == PinSide.LEFT:
            return _clock_triangle(x + border_offset, y)
        return _clock_triangle(x - border_offset, y, flip=True)
    if pin.decorator == DecoratorType.ACTIVE_LOW:
        if side == PinSide.LEFT:
            return _inversion_bubble(x - 3, y)
        return _inversion_bubble(x + 3, y)
    if pin.decorator == DecoratorType.INTERFACE:
        if side == PinSide.LEFT:
            return _interface_diamond(x - 5, y)
        return _interface_diamond(x + 5, y)
    if pin.decorator == DecoratorType.INOUT:
        if side == PinSide.RIGHT:
            return _inout_arrow(x + 8, y)
        return _inout_arrow(x - 8, y)
    return ""


def render_svg(
    layout: LayoutSpec,
    theme: dict[str, str] | None = None,
    options: RenderOptions | None = None,
) -> str:
    """Render a LayoutSpec as an SVG string.

    Args:
        layout: Computed layout geometry.
        theme: CSS variable overrides. Merged with DEFAULT_THEME.
        options: Rendering options.

    Returns:
        Complete SVG string.
    """
    if options is None:
        options = RenderOptions()

    merged_theme = dict(DEFAULT_THEME)
    if theme:
        merged_theme.update(theme)

    parts: list[str] = []

    # SVG envelope — expand viewBox by half the border stroke-width
    # so that box border strokes are not clipped at the viewport edge.
    stroke_pad = 0.75  # half of the 1.5 border stroke-width
    w = _fmt(layout.total_width + 2 * stroke_pad)
    h = _fmt(layout.total_height + 2 * stroke_pad)
    vb = (
        f"{_fmt(-stroke_pad)} {_fmt(-stroke_pad)} {w} {h}"
    )
    if options.standalone:
        parts.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{w}" height="{h}" '
            f'viewBox="{vb}" class="svblock">'
        )
    else:
        parts.append(
            f'<svg width="{w}" height="{h}" '
            f'viewBox="{vb}" class="svblock">'
        )

    # CSS
    parts.append(_css_block(merged_theme))

    # Module box — fill drawn first, then header, then border on top
    # so the border has uniform thickness on all sides.
    parts.append(
        f'  <rect x="{_fmt(layout.box_x)}" y="{_fmt(layout.box_y)}" '
        f'width="{_fmt(layout.box_width)}" '
        f'height="{_fmt(layout.box_height)}" '
        f'class="svblock-box-fill"/>'
    )

    # Header background (fill only)
    hr = layout.header_rect
    parts.append(
        f'  <rect x="{_fmt(hr.x)}" y="{_fmt(hr.y)}" '
        f'width="{_fmt(hr.width)}" height="{_fmt(hr.height)}" '
        f'class="svblock-header"/>'
    )
    # Header bottom separator line
    parts.append(
        f'  <line x1="{_fmt(hr.x)}" y1="{_fmt(hr.y + hr.height)}" '
        f'x2="{_fmt(hr.x + hr.width)}" y2="{_fmt(hr.y + hr.height)}" '
        f'stroke="var(--sym-border)" stroke-width="0.5"/>'
    )

    # Module box border — drawn after header so it is uniformly visible
    parts.append(
        f'  <rect x="{_fmt(layout.box_x)}" y="{_fmt(layout.box_y)}" '
        f'width="{_fmt(layout.box_width)}" '
        f'height="{_fmt(layout.box_height)}" '
        f'class="svblock-box-border"/>'
    )

    # Module name
    name_x = hr.x + hr.width / 2
    name_y = hr.y + 22
    parts.append(
        f'  <text x="{_fmt(name_x)}" y="{_fmt(name_y)}" '
        f'text-anchor="middle" class="svblock-name" '
        f'id="module-{layout.module_name}">'
        f'{layout.module_name}</text>'
    )

    # Parameters
    if not options.no_params and layout.params_text:
        for i, param_text in enumerate(layout.params_text):
            py = hr.y + 36 + i * 16
            words = param_text.split()
            pid = words[1] if len(words) > 1 else words[0]
            parts.append(
                f'  <text x="{_fmt(name_x)}" '
                f'y="{_fmt(py)}" '
                f'text-anchor="middle" '
                f'class="svblock-param" '
                f'id="param-{pid}">'
                f'{param_text}</text>'
            )

    # Group separators
    for sep in layout.group_separators:
        parts.append(
            f'  <line x1="{_fmt(layout.box_x)}" '
            f'y1="{_fmt(sep.y)}" '
            f'x2="{_fmt(layout.box_x + layout.box_width)}" '
            f'y2="{_fmt(sep.y)}" '
            f'class="svblock-group-sep" '
            f'id="group-{sep.label}"/>'
        )
        label_x = layout.box_x + layout.box_width / 2
        label_y = sep.y + 13
        parts.append(
            f'  <text x="{_fmt(label_x)}" y="{_fmt(label_y)}" '
            f'class="svblock-group-label">{sep.label}</text>'
        )

    # Pin rows
    for pin in layout.pin_rows:
        color_class = _port_css_class(pin)
        stroke_class = _pin_stroke_class(pin)

        if pin.side == PinSide.LEFT:
            # Pin line: from left edge to box
            line_x1 = 0.0
            line_x2 = layout.box_x
            label_x = layout.box_x + 8
            anchor = "start"
        else:
            # Pin line: from box right edge to right
            line_x1 = layout.box_x + layout.box_width
            line_x2 = layout.total_width
            label_x = layout.box_x + layout.box_width - 8
            anchor = "end"

        # Pin line
        parts.append(
            f'  <line x1="{_fmt(line_x1)}" y1="{_fmt(pin.y)}" '
            f'x2="{_fmt(line_x2)}" y2="{_fmt(pin.y)}" '
            f'class="{stroke_class}" stroke="{color_class}" '
            f'id="port-{pin.port_name}"/>'
        )

        # Port label
        label = pin.label_text
        if pin.bus_label:
            label = f"{pin.label_text} {pin.bus_label}"
        parts.append(
            f'  <text x="{_fmt(label_x)}" y="{_fmt(pin.y + 4)}" '
            f'text-anchor="{anchor}" class="svblock-port {color_class}">'
            f'<title>{pin.port_name}</title>{label}</text>'
        )

        # Decorator
        if not options.no_decorators:
            decorator_x = line_x2 if pin.side == PinSide.LEFT else line_x1
            dec_svg = _render_decorator(
                pin, decorator_x, pin.y, pin.side
            )
            if dec_svg:
                parts.append(f"  {dec_svg}")

    parts.append("</svg>")
    return "\n".join(parts)
