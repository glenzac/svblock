"""SVG renderer for block diagrams showing nested module instances."""

from __future__ import annotations

from svblock.layout.block_layout import (
    Arrow,
    BlockLayoutSpec,
    InstanceBox,
    ParentPortStub,
)
from svblock.model import PortDirection

# Default theme additions for block diagrams.
BLOCK_THEME_DEFAULTS: dict[str, str] = {
    "--sym-arrow": "#555555",
    "--sym-instance-bg": "#f8f8f8",
    "--sym-instance-border": "#333333",
    "--sym-parent-border": "#999999",
    "--sym-parent-bg": "#ffffff",
}


def _fmt(v: float) -> str:
    """Format a float to 2 decimal places, stripping trailing zeros."""
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _merge_block_theme(theme: dict[str, str]) -> dict[str, str]:
    """Merge block-diagram defaults into a theme, without overwriting."""
    merged = dict(BLOCK_THEME_DEFAULTS)
    merged.update(theme)
    return merged


def _css_block(theme: dict[str, str]) -> str:
    """Generate the CSS style block for block diagrams."""
    variables = "\n".join(
        f"      {k}: {v};" for k, v in theme.items()
    )
    rules = [
        ".svblock-block-parent { fill: var(--sym-parent-bg); "
        "stroke: var(--sym-parent-border); stroke-width: 2; "
        "stroke-dasharray: 8,4; }",
        ".svblock-block-instance { fill: var(--sym-instance-bg); "
        "stroke: var(--sym-instance-border); stroke-width: 1.5; "
        "rx: 4; ry: 4; }",
        ".svblock-block-instance-label { font-family: sans-serif; "
        "font-size: 13px; fill: var(--sym-text); "
        "text-anchor: middle; dominant-baseline: central; }",
        ".svblock-block-module-label { font-family: monospace; "
        "font-size: 11px; fill: var(--sym-param-text); "
        "text-anchor: middle; dominant-baseline: central; }",
        ".svblock-block-parent-label { font-family: sans-serif; "
        "font-size: 16px; font-weight: bold; "
        "fill: var(--sym-text); }",
        ".svblock-block-arrow { stroke: var(--sym-arrow); "
        "fill: none; }",
        ".svblock-block-port-label { font-family: monospace; "
        "font-size: 12px; fill: var(--sym-text); }",
        ".svblock-block-port-line { stroke: var(--sym-arrow); "
        "stroke-width: 1.5; stroke-dasharray: 6,3; }",
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


def _arrow_markers(theme: dict[str, str], stroke_width: float) -> str:
    """Generate SVG marker definitions for arrowheads."""
    color = theme.get("--sym-arrow", "#555555")
    return (
        "    <defs>\n"
        f'      <marker id="arrow-end" markerWidth="10" markerHeight="8" '
        f'refX="9" refY="4" orient="auto" markerUnits="userSpaceOnUse">\n'
        f'        <path d="M0,0 L10,4 L0,8 Z" fill="{color}"/>\n'
        f"      </marker>\n"
        f'      <marker id="arrow-start" markerWidth="10" markerHeight="8" '
        f'refX="1" refY="4" orient="auto" markerUnits="userSpaceOnUse">\n'
        f'        <path d="M10,0 L0,4 L10,8 Z" fill="{color}"/>\n'
        f"      </marker>\n"
        f'      <marker id="port-arrow" markerWidth="8" markerHeight="6" '
        f'refX="7" refY="3" orient="auto" markerUnits="userSpaceOnUse">\n'
        f'        <path d="M0,0 L8,3 L0,6 Z" fill="{color}"/>\n'
        f"      </marker>\n"
        "    </defs>"
    )


def _render_parent_box(layout: BlockLayoutSpec) -> str:
    """Render the parent module boundary rectangle and label."""
    lines: list[str] = []
    lines.append(
        f'    <rect class="svblock-block-parent" '
        f'x="{_fmt(layout.parent_x)}" y="{_fmt(layout.parent_y)}" '
        f'width="{_fmt(layout.parent_width)}" '
        f'height="{_fmt(layout.parent_height)}" '
        f'rx="6" ry="6"/>'
    )
    # Parent label at top-left inside the boundary
    label_x = layout.parent_x + 12
    label_y = layout.parent_y + 20
    lines.append(
        f'    <text class="svblock-block-parent-label" '
        f'x="{_fmt(label_x)}" y="{_fmt(label_y)}">'
        f"{layout.parent_name}</text>"
    )
    return "\n".join(lines)


def _render_instance(box: InstanceBox) -> str:
    """Render a single instance box with its name and module type."""
    lines: list[str] = []
    cx = box.x + box.width / 2
    cy = box.y + box.height / 2

    lines.append(
        f'    <rect class="svblock-block-instance" '
        f'id="inst-{box.instance_name}" '
        f'x="{_fmt(box.x)}" y="{_fmt(box.y)}" '
        f'width="{_fmt(box.width)}" height="{_fmt(box.height)}"/>'
    )
    # Instance name (top line)
    lines.append(
        f'    <text class="svblock-block-instance-label" '
        f'x="{_fmt(cx)}" y="{_fmt(cy - 7)}">'
        f"{box.instance_name}</text>"
    )
    # Module type (bottom line, smaller)
    lines.append(
        f'    <text class="svblock-block-module-label" '
        f'x="{_fmt(cx)}" y="{_fmt(cy + 9)}">'
        f"{box.module_name}</text>"
    )
    return "\n".join(lines)


def _render_arrow(arrow: Arrow, stroke_width: float) -> str:
    """Render a connection arrow between two instances."""
    sw = _fmt(stroke_width)
    marker = 'marker-end="url(#arrow-end)"'
    if arrow.bidirectional:
        marker += ' marker-start="url(#arrow-start)"'

    return (
        f'    <line class="svblock-block-arrow" '
        f'x1="{_fmt(arrow.from_x)}" y1="{_fmt(arrow.from_y)}" '
        f'x2="{_fmt(arrow.to_x)}" y2="{_fmt(arrow.to_y)}" '
        f'stroke-width="{sw}" {marker}/>'
    )


def _render_port_stub(stub: ParentPortStub) -> str:
    """Render a parent port stub with a label and dashed line."""
    lines: list[str] = []

    # Dashed line from parent boundary to child instance
    marker = 'marker-end="url(#port-arrow)"'
    if stub.direction == PortDirection.OUTPUT:
        marker = 'marker-end="url(#port-arrow)"'

    lines.append(
        f'    <line class="svblock-block-port-line" '
        f'x1="{_fmt(stub.line_x1)}" y1="{_fmt(stub.line_y1)}" '
        f'x2="{_fmt(stub.line_x2)}" y2="{_fmt(stub.line_y2)}" '
        f'{marker}/>'
    )

    # Port label
    if stub.direction in (PortDirection.INPUT, PortDirection.INOUT):
        anchor = "end"
    else:
        anchor = "start"

    lines.append(
        f'    <text class="svblock-block-port-label" '
        f'x="{_fmt(stub.label_x)}" y="{_fmt(stub.label_y)}" '
        f'text-anchor="{anchor}" dominant-baseline="central">'
        f"{stub.port_name}</text>"
    )
    return "\n".join(lines)


def render_block_svg(
    layout: BlockLayoutSpec,
    theme: dict[str, str] | None = None,
    standalone: bool = True,
    arrow_stroke_width: float = 3.0,
) -> str:
    """Render a block diagram layout as an SVG string.

    Args:
        layout: The computed block layout specification.
        theme: CSS variable theme dict. Merged with block defaults.
        standalone: If True, include xmlns for standalone SVG file.
        arrow_stroke_width: Stroke width for connection arrows.

    Returns:
        Complete SVG string.
    """
    merged_theme = _merge_block_theme(theme or {})

    parts: list[str] = []

    # SVG root
    xmlns = ' xmlns="http://www.w3.org/2000/svg"' if standalone else ""
    parts.append(
        f'<svg{xmlns} '
        f'width="{_fmt(layout.total_width)}" '
        f'height="{_fmt(layout.total_height)}" '
        f'viewBox="0 0 {_fmt(layout.total_width)} {_fmt(layout.total_height)}">'
    )

    # CSS
    parts.append(_css_block(merged_theme))

    # Arrow markers
    parts.append(_arrow_markers(merged_theme, arrow_stroke_width))

    # Parent box
    parts.append(_render_parent_box(layout))

    # Instance boxes
    for box in layout.instance_boxes:
        parts.append(_render_instance(box))

    # Arrows
    for arrow in layout.arrows:
        parts.append(_render_arrow(arrow, arrow_stroke_width))

    # Parent port stubs
    for stub in layout.parent_port_stubs:
        parts.append(_render_port_stub(stub))

    parts.append("</svg>")
    return "\n".join(parts)
