"""Layout engine: computes box geometry and pin coordinates."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from svblock.layout.text_metrics import measure_text
from svblock.model import GroupDef, ModuleIR, PortDirection


class PinSide(Enum):
    LEFT = "left"
    RIGHT = "right"


class DecoratorType(Enum):
    NONE = "none"
    CLOCK = "clock"
    ACTIVE_LOW = "active_low"
    BUS = "bus"
    INTERFACE = "interface"
    INOUT = "inout"


@dataclass
class PinRow:
    port_name: str
    side: PinSide
    y: float
    label_text: str
    decorator: DecoratorType
    bus_label: str | None = None
    group_name: str | None = None


@dataclass
class GroupSeparator:
    y: float
    label: str


@dataclass
class HeaderRect:
    x: float
    y: float
    width: float
    height: float


@dataclass
class LayoutConfig:
    pin_row_height: float = 20.0
    interface_row_height: float = 28.0
    group_header_height: float = 18.0
    header_base_height: float = 36.0
    header_param_line_height: float = 16.0
    min_box_width: float = 240.0
    box_padding: float = 12.0
    pin_label_padding: float = 8.0
    pin_stub_length: float = 30.0
    decorator_width: float = 12.0
    port_font_size: float = 13.0
    header_font_size: float = 15.0
    group_font_size: float = 11.0
    param_font_size: float = 11.0
    no_params: bool = False
    no_groups: bool = False
    no_decorators: bool = False


@dataclass
class LayoutSpec:
    box_x: float
    box_y: float
    box_width: float
    box_height: float
    header_rect: HeaderRect
    module_name: str
    params_text: list[str]
    pin_rows: list[PinRow] = field(default_factory=list)
    group_separators: list[GroupSeparator] = field(default_factory=list)
    total_width: float = 0.0
    total_height: float = 0.0


def _get_decorator(port_name: str, port: object) -> DecoratorType:
    """Determine the decorator type for a port."""
    from svblock.model import PortDef

    if not isinstance(port, PortDef):
        return DecoratorType.NONE
    if port.is_interface:
        return DecoratorType.INTERFACE
    if port.direction == PortDirection.INOUT:
        return DecoratorType.INOUT
    if port.is_bus:
        return DecoratorType.BUS
    if port.has_clock_marker:
        return DecoratorType.CLOCK
    if port.has_active_low_marker:
        return DecoratorType.ACTIVE_LOW
    return DecoratorType.NONE


def _get_bus_label(port: object) -> str | None:
    """Get the bus range label for display."""
    from svblock.model import PortDef

    if not isinstance(port, PortDef):
        return None
    if port.is_bus and port.bus_range:
        left, right = port.bus_range
        return f"[{left}:{right}]"
    return None


def _pin_side(port: object) -> PinSide:
    """Determine which side of the box a port goes on."""
    from svblock.model import PortDef

    if not isinstance(port, PortDef):
        return PinSide.LEFT
    if port.direction in (
        PortDirection.OUTPUT,
        PortDirection.INOUT,
        PortDirection.INTERFACE,
    ):
        return PinSide.RIGHT
    return PinSide.LEFT


def _row_height(port: object, config: LayoutConfig) -> float:
    """Get the row height for a port."""
    from svblock.model import PortDef

    if isinstance(port, PortDef) and port.is_interface:
        return config.interface_row_height
    return config.pin_row_height


def compute_layout(
    module: ModuleIR,
    config: LayoutConfig | None = None,
) -> LayoutSpec:
    """Compute the full layout geometry for a module symbol.

    Args:
        module: A ModuleIR with groups already assigned.
        config: Layout configuration. Uses defaults if None.

    Returns:
        A LayoutSpec with all coordinates computed.
    """
    if config is None:
        config = LayoutConfig()

    port_map = {p.name: p for p in module.ports}

    # Header height
    params_text: list[str] = []
    if not config.no_params:
        for param in module.params:
            val = f" = {param.default_value}" if param.default_value else ""
            params_text.append(f"{param.param_type} {param.name}{val}")

    header_height = config.header_base_height
    if params_text:
        header_height += len(params_text) * config.header_param_line_height

    # Compute max label widths for box sizing
    left_labels: list[str] = []
    right_labels: list[str] = []
    for port in module.ports:
        side = _pin_side(port)
        label = port.name
        bus_label = _get_bus_label(port)
        if bus_label:
            label = f"{port.name} {bus_label}"
        if side == PinSide.LEFT:
            left_labels.append(label)
        else:
            right_labels.append(label)

    max_left = max(
        (measure_text(lb, config.port_font_size) for lb in left_labels),
        default=0.0,
    )
    max_right = max(
        (measure_text(lb, config.port_font_size) for lb in right_labels),
        default=0.0,
    )
    module_name_width = measure_text(
        module.name, config.header_font_size, "proportional"
    )

    # Box width
    content_width = (
        max_left
        + max_right
        + module_name_width
        + config.box_padding * 4
        + config.pin_label_padding * 2
    )
    box_width = max(content_width, config.min_box_width)

    # Box position (leave room for pin stubs)
    box_x = config.pin_stub_length
    box_y = 0.0

    # Place pins by iterating through groups
    pin_rows: list[PinRow] = []
    group_separators: list[GroupSeparator] = []
    current_y = box_y + header_height

    groups = module.groups if module.groups else [
        GroupDef(name="Ports", port_names=[p.name for p in module.ports])
    ]

    for group_idx, group in enumerate(groups):
        # Add group separator (except before the first group)
        if group_idx > 0 and not config.no_groups:
            group_separators.append(
                GroupSeparator(y=current_y, label=group.label or group.name)
            )
            current_y += config.group_header_height

        # Separate left/right ports in this group
        left_ports: list[str] = []
        right_ports: list[str] = []
        for pname in group.port_names:
            if pname in port_map:
                port = port_map[pname]
                if _pin_side(port) == PinSide.LEFT:
                    left_ports.append(pname)
                else:
                    right_ports.append(pname)

        # Place pins, tracking y on each side
        left_y = current_y
        right_y = current_y

        for pname in left_ports:
            port = port_map[pname]
            h = _row_height(port, config)
            pin_rows.append(PinRow(
                port_name=pname,
                side=PinSide.LEFT,
                y=left_y + h / 2,  # center of row
                label_text=pname,
                decorator=_get_decorator(pname, port),
                bus_label=_get_bus_label(port),
                group_name=group.name,
            ))
            left_y += h

        for pname in right_ports:
            port = port_map[pname]
            h = _row_height(port, config)
            pin_rows.append(PinRow(
                port_name=pname,
                side=PinSide.RIGHT,
                y=right_y + h / 2,
                label_text=pname,
                decorator=_get_decorator(pname, port),
                bus_label=_get_bus_label(port),
                group_name=group.name,
            ))
            right_y += h

        current_y = max(left_y, right_y)

    # Box height
    box_height = current_y - box_y
    # Ensure minimum height for header
    box_height = max(box_height, header_height + config.pin_row_height)

    # Total canvas size
    total_width = box_x + box_width + config.pin_stub_length
    total_height = box_height

    return LayoutSpec(
        box_x=box_x,
        box_y=box_y,
        box_width=box_width,
        box_height=box_height,
        header_rect=HeaderRect(
            x=box_x,
            y=box_y,
            width=box_width,
            height=header_height,
        ),
        module_name=module.name,
        params_text=params_text,
        pin_rows=pin_rows,
        group_separators=group_separators,
        total_width=total_width,
        total_height=total_height,
    )
