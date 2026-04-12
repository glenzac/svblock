"""Layout engine for block diagrams showing nested module instances."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field

from svblock.layout.text_metrics import measure_text
from svblock.model import BlockDiagramIR, PortDirection


@dataclass
class BlockLayoutConfig:
    """Configuration for block diagram layout."""

    instance_box_min_width: float = 140.0
    instance_box_height: float = 50.0
    instance_box_padding: float = 20.0
    parent_padding: float = 60.0
    instance_spacing_x: float = 100.0
    instance_spacing_y: float = 40.0
    arrow_stroke_width: float = 3.0
    parent_port_stub_length: float = 40.0
    font_size: float = 14.0
    parent_label_font_size: float = 16.0
    parent_label_height: float = 30.0
    show_parent_ports: bool = False


@dataclass
class InstanceBox:
    """Positioned instance box in the layout."""

    instance_name: str
    module_name: str
    x: float
    y: float
    width: float
    height: float


@dataclass
class Arrow:
    """Arrow connecting two instance boxes."""

    from_x: float
    from_y: float
    to_x: float
    to_y: float
    bidirectional: bool = False


@dataclass
class ParentPortStub:
    """A parent port drawn on the parent boundary with a line to a child instance."""

    port_name: str
    direction: PortDirection
    label_x: float
    label_y: float
    line_x1: float
    line_y1: float
    line_x2: float
    line_y2: float


@dataclass
class BlockLayoutSpec:
    """Complete layout specification for a block diagram."""

    parent_name: str
    parent_x: float
    parent_y: float
    parent_width: float
    parent_height: float
    instance_boxes: list[InstanceBox] = field(default_factory=list)
    arrows: list[Arrow] = field(default_factory=list)
    parent_port_stubs: list[ParentPortStub] = field(default_factory=list)
    total_width: float = 0.0
    total_height: float = 0.0
    show_parent_ports: bool = False


def _topological_columns(ir: BlockDiagramIR) -> dict[str, int]:
    """Assign instances to columns via topological ordering.

    Instances with no incoming connections go to column 0,
    their direct dependents to column 1, and so on.
    """
    instance_names = {inst.instance_name for inst in ir.instances}

    # Build adjacency for non-bidirectional edges
    incoming: dict[str, set[str]] = defaultdict(set)
    outgoing: dict[str, set[str]] = defaultdict(set)

    for conn in ir.connections:
        if conn.is_bidirectional:
            continue
        if conn.from_instance in instance_names and conn.to_instance in instance_names:
            outgoing[conn.from_instance].add(conn.to_instance)
            incoming[conn.to_instance].add(conn.from_instance)

    # BFS-based longest path (gives column = longest path from a source)
    columns: dict[str, int] = {}
    for inst in ir.instances:
        columns[inst.instance_name] = 0

    queue: deque[str] = deque()
    for inst in ir.instances:
        if not incoming[inst.instance_name]:
            queue.append(inst.instance_name)

    visited: set[str] = set()
    while queue:
        name = queue.popleft()
        if name in visited:
            continue
        visited.add(name)
        for dep in outgoing[name]:
            columns[dep] = max(columns[dep], columns[name] + 1)
            queue.append(dep)

    # Assign unvisited instances (e.g. in bidirectional-only cycles) to column 0
    for inst in ir.instances:
        if inst.instance_name not in visited:
            columns[inst.instance_name] = 0

    return columns


def _compute_instance_width(
    module_name: str,
    instance_name: str,
    font_size: float,
    min_width: float,
    padding: float,
) -> float:
    """Compute instance box width based on label text."""
    label = f"{instance_name} ({module_name})"
    text_width = measure_text(label, font_size, "proportional")
    return max(min_width, text_width + padding * 2)


def compute_block_layout(
    ir: BlockDiagramIR,
    config: BlockLayoutConfig | None = None,
) -> BlockLayoutSpec:
    """Compute the block diagram layout from a BlockDiagramIR.

    Places instances in topologically-ordered columns, draws arrows
    between connected instances, and optionally adds parent port stubs.
    """
    if config is None:
        config = BlockLayoutConfig()

    if not ir.instances:
        return BlockLayoutSpec(
            parent_name=ir.parent_name,
            parent_x=0,
            parent_y=0,
            parent_width=config.instance_box_min_width + config.parent_padding * 2,
            parent_height=config.instance_box_height + config.parent_padding * 2,
            total_width=config.instance_box_min_width + config.parent_padding * 2,
            total_height=config.instance_box_height + config.parent_padding * 2,
            show_parent_ports=config.show_parent_ports,
        )

    # Step 1: Topological column assignment
    columns = _topological_columns(ir)

    # Step 2: Group instances by column
    col_groups: dict[int, list[str]] = defaultdict(list)
    for inst in ir.instances:
        col_groups[columns[inst.instance_name]].append(inst.instance_name)

    max_col = max(col_groups.keys()) if col_groups else 0

    # Step 3: Compute box sizes
    box_widths: dict[str, float] = {}
    for inst in ir.instances:
        box_widths[inst.instance_name] = _compute_instance_width(
            inst.module_name,
            inst.instance_name,
            config.font_size,
            config.instance_box_min_width,
            config.instance_box_padding,
        )

    # Step 4: Compute column x-positions
    col_x: dict[int, float] = {}
    col_widths: dict[int, float] = {}
    x_cursor = config.parent_padding
    if config.show_parent_ports:
        x_cursor += config.parent_port_stub_length + 20

    for col in range(max_col + 1):
        col_x[col] = x_cursor
        max_w = max(
            (box_widths[n] for n in col_groups[col]),
            default=config.instance_box_min_width,
        )
        col_widths[col] = max_w
        x_cursor += max_w + config.instance_spacing_x

    # Step 5: Compute y-positions (center each column vertically)
    box_positions: dict[str, tuple[float, float]] = {}

    # Find max column height for vertical centering
    col_heights: dict[int, float] = {}
    for col in range(max_col + 1):
        n = len(col_groups[col])
        col_heights[col] = (
            n * config.instance_box_height + (n - 1) * config.instance_spacing_y
        )

    max_height = (
        max(col_heights.values()) if col_heights
        else config.instance_box_height
    )

    y_start = config.parent_padding + config.parent_label_height

    for col in range(max_col + 1):
        names = col_groups[col]
        total_h = col_heights[col]
        y_offset = y_start + (max_height - total_h) / 2

        cx = col_x[col]
        cw = col_widths[col]
        for i, name in enumerate(names):
            bw = box_widths[name]
            bx = cx + (cw - bw) / 2  # center within column
            by = y_offset + i * (config.instance_box_height + config.instance_spacing_y)
            box_positions[name] = (bx, by)

    # Step 6: Build InstanceBox objects
    instance_boxes: list[InstanceBox] = []
    for inst in ir.instances:
        bx, by = box_positions[inst.instance_name]
        instance_boxes.append(InstanceBox(
            instance_name=inst.instance_name,
            module_name=inst.module_name,
            x=bx,
            y=by,
            width=box_widths[inst.instance_name],
            height=config.instance_box_height,
        ))

    # Step 7: Build arrows between instances
    arrows: list[Arrow] = []
    for conn in ir.connections:
        from_box = next(
            (b for b in instance_boxes if b.instance_name == conn.from_instance), None
        )
        to_box = next(
            (b for b in instance_boxes if b.instance_name == conn.to_instance), None
        )
        if from_box is None or to_box is None:
            continue

        # Connect from right edge of source to left edge of target
        from_col = columns[conn.from_instance]
        to_col = columns[conn.to_instance]

        if from_col < to_col:
            fx = from_box.x + from_box.width
            fy = from_box.y + from_box.height / 2
            tx = to_box.x
            ty = to_box.y + to_box.height / 2
        elif from_col > to_col:
            fx = from_box.x
            fy = from_box.y + from_box.height / 2
            tx = to_box.x + to_box.width
            ty = to_box.y + to_box.height / 2
        else:
            # Same column: connect bottom of one to top of other
            if from_box.y < to_box.y:
                fx = from_box.x + from_box.width / 2
                fy = from_box.y + from_box.height
                tx = to_box.x + to_box.width / 2
                ty = to_box.y
            else:
                fx = from_box.x + from_box.width / 2
                fy = from_box.y
                tx = to_box.x + to_box.width / 2
                ty = to_box.y + to_box.height

        arrows.append(Arrow(
            from_x=fx,
            from_y=fy,
            to_x=tx,
            to_y=ty,
            bidirectional=conn.is_bidirectional,
        ))

    # Step 8: Compute parent boundary
    all_right = max(
        (b.x + b.width for b in instance_boxes),
        default=config.instance_box_min_width,
    )
    all_bottom = max(
        (b.y + b.height for b in instance_boxes),
        default=config.instance_box_height,
    )

    parent_x = 0.0
    parent_y = 0.0
    parent_width = all_right + config.parent_padding
    if config.show_parent_ports:
        parent_width += config.parent_port_stub_length + 20
    parent_height = all_bottom + config.parent_padding

    # Step 9: Parent port stubs (optional)
    parent_port_stubs: list[ParentPortStub] = []
    if config.show_parent_ports and ir.parent_port_instances:
        input_dirs = (PortDirection.INPUT, PortDirection.INOUT)
        input_ports = [
            p for p in ir.parent_port_instances
            if ir.parent_port_directions.get(p) in input_dirs
        ]
        output_ports = [
            p for p in ir.parent_port_instances
            if ir.parent_port_directions.get(p) == PortDirection.OUTPUT
        ]

        # Place input ports on the left edge
        if input_ports:
            spacing = parent_height / (len(input_ports) + 1)
            for i, pname in enumerate(input_ports):
                py = spacing * (i + 1)
                stub_x = parent_x
                label_x = parent_x - 5
                # Find the first connected instance
                connected = ir.parent_port_instances.get(pname, [])
                if connected:
                    target = next(
                        (b for b in instance_boxes if b.instance_name == connected[0]),
                        None,
                    )
                    if target:
                        pdir = ir.parent_port_directions.get(
                            pname, PortDirection.INPUT,
                        )
                        parent_port_stubs.append(ParentPortStub(
                            port_name=pname,
                            direction=pdir,
                            label_x=label_x,
                            label_y=py,
                            line_x1=stub_x,
                            line_y1=py,
                            line_x2=target.x,
                            line_y2=target.y + target.height / 2,
                        ))

        # Place output ports on the right edge
        if output_ports:
            spacing = parent_height / (len(output_ports) + 1)
            for i, pname in enumerate(output_ports):
                py = spacing * (i + 1)
                stub_x = parent_width
                label_x = parent_width + 5
                connected = ir.parent_port_instances.get(pname, [])
                if connected:
                    target = next(
                        (b for b in instance_boxes if b.instance_name == connected[0]),
                        None,
                    )
                    if target:
                        pdir = ir.parent_port_directions.get(
                            pname, PortDirection.OUTPUT,
                        )
                        parent_port_stubs.append(ParentPortStub(
                            port_name=pname,
                            direction=pdir,
                            label_x=label_x,
                            label_y=py,
                            line_x1=target.x + target.width,
                            line_y1=target.y + target.height / 2,
                            line_x2=stub_x,
                            line_y2=py,
                        ))

    # Total canvas size
    total_width = parent_width
    total_height = parent_height

    # Expand for port labels if needed
    if parent_port_stubs:
        max_label_w = max(
            measure_text(s.port_name, config.font_size, "monospace")
            for s in parent_port_stubs
        )
        total_width += max_label_w + 10

    return BlockLayoutSpec(
        parent_name=ir.parent_name,
        parent_x=parent_x,
        parent_y=parent_y,
        parent_width=parent_width,
        parent_height=parent_height,
        instance_boxes=instance_boxes,
        arrows=arrows,
        parent_port_stubs=parent_port_stubs,
        total_width=total_width,
        total_height=total_height,
        show_parent_ports=config.show_parent_ports,
    )
