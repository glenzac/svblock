"""Heuristic port grouping when no @sym annotations are present."""

from __future__ import annotations

import re
from dataclasses import replace

from svblock.model import GroupDef, ModuleIR, PortDirection

_CLOCK_RE = re.compile(r"^(clk|clock)$|_clk$|_clock$", re.IGNORECASE)
_RESET_RE = re.compile(r"^(rst|reset)", re.IGNORECASE)


def apply_grouping(module: ModuleIR, *, flat: bool = False) -> ModuleIR:
    """Assign ports to groups and return a new ModuleIR with groups populated.

    Explicit annotation groups (port.group is not None) are preserved.
    Remaining ports are grouped by heuristic name patterns.

    Args:
        module: Input ModuleIR (not mutated).
        flat: If True, put all ports in a single default group.

    Returns:
        A new ModuleIR with groups fully populated.
    """
    if flat:
        group = GroupDef(
            name="Ports",
            port_names=[p.name for p in module.ports],
        )
        return replace(module, groups=[group])

    # Separate annotated groups from unannotated ports
    explicit_groups: dict[str, list[str]] = {}
    ungrouped: list[str] = []

    for port in module.ports:
        if port.group is not None:
            explicit_groups.setdefault(port.group, []).append(port.name)
        else:
            ungrouped.append(port.name)

    # Build a lookup for port direction by name
    port_map = {p.name: p for p in module.ports}

    # Heuristic buckets for ungrouped ports
    clocks: list[str] = []
    resets: list[str] = []
    inputs: list[str] = []
    outputs: list[str] = []
    interfaces: list[str] = []

    for name in ungrouped:
        port = port_map[name]
        if port.is_interface:
            interfaces.append(name)
        elif _CLOCK_RE.search(name):
            clocks.append(name)
        elif _RESET_RE.search(name):
            resets.append(name)
        elif port.direction in (PortDirection.OUTPUT, PortDirection.INOUT):
            outputs.append(name)
        else:
            inputs.append(name)

    # Build ordered group list: explicit first (in declaration order),
    # then heuristic groups
    groups: list[GroupDef] = []

    # Preserve explicit group order by first port appearance
    for group_name, port_names in explicit_groups.items():
        groups.append(GroupDef(name=group_name, port_names=port_names))

    # Add heuristic groups (only if non-empty)
    heuristic = [
        ("Clocks", clocks),
        ("Resets", resets),
        ("Inputs", inputs),
        ("Outputs", outputs),
        ("Interfaces", interfaces),
    ]
    for group_name, port_names in heuristic:
        if port_names:
            groups.append(GroupDef(name=group_name, port_names=port_names))

    return replace(module, groups=groups)
