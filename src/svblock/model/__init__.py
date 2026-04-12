"""Data model: ModuleIR, PortDef, ParamDef, GroupDef, BlockDiagramIR."""

from __future__ import annotations

from svblock.model.block_ir import BlockDiagramIR, ConnectionDef, InstanceDef
from svblock.model.module_ir import GroupDef, ModuleIR, ParamDef, PortDef
from svblock.model.port_types import PortDirection

__all__ = [
    "BlockDiagramIR",
    "ConnectionDef",
    "GroupDef",
    "InstanceDef",
    "ModuleIR",
    "ParamDef",
    "PortDef",
    "PortDirection",
]
