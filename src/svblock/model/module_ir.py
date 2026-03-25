"""Intermediate representation for parsed SystemVerilog modules."""

from __future__ import annotations

from dataclasses import dataclass, field

from svblock.model.port_types import PortDirection


@dataclass
class PortDef:
    """Definition of a single module port."""

    name: str
    direction: PortDirection
    port_type: str = "logic"
    is_bus: bool = False
    bus_range: tuple[str, str] | None = None
    is_interface: bool = False
    modport: str | None = None
    group: str | None = None
    has_clock_marker: bool = False
    has_active_low_marker: bool = False


@dataclass
class ParamDef:
    """Definition of a single module parameter."""

    name: str
    param_type: str = "integer"
    default_value: str | None = None
    is_localparam: bool = False


@dataclass
class GroupDef:
    """A named group of ports for visual grouping in the diagram."""

    name: str
    label: str | None = None
    port_names: list[str] = field(default_factory=list)


@dataclass
class ModuleIR:
    """Intermediate representation of a parsed SystemVerilog module."""

    name: str
    file_path: str
    ports: list[PortDef] = field(default_factory=list)
    params: list[ParamDef] = field(default_factory=list)
    groups: list[GroupDef] = field(default_factory=list)

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for port in self.ports:
            if port.name in seen:
                raise ValueError(f"Duplicate port name: '{port.name}'")
            seen.add(port.name)
