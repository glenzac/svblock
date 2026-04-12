"""Intermediate representation for block diagrams with nested module instances."""

from __future__ import annotations

from dataclasses import dataclass, field

from svblock.model.port_types import PortDirection


@dataclass
class InstanceDef:
    """A module instance within a parent module."""

    instance_name: str
    module_name: str


@dataclass
class ConnectionDef:
    """A connection between two instances, or between a parent port and an instance."""

    from_instance: str
    to_instance: str
    is_bidirectional: bool = False


@dataclass
class BlockDiagramIR:
    """Block diagram IR: nested module instances and connections."""

    parent_name: str
    file_path: str
    instances: list[InstanceDef] = field(default_factory=list)
    connections: list[ConnectionDef] = field(default_factory=list)
    parent_port_instances: dict[str, list[str]] = field(default_factory=dict)
    parent_port_directions: dict[str, PortDirection] = field(default_factory=dict)
