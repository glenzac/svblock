"""Port direction enum for SystemVerilog module ports."""

from __future__ import annotations

from enum import Enum


class PortDirection(Enum):
    """Direction of a module port."""

    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"
    INTERFACE = "interface"
    REF = "ref"
