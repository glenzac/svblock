"""SystemVerilog parsing and annotation extraction."""

from __future__ import annotations

from svblock.parser.hierarchy_extractor import extract_block_diagram
from svblock.parser.sv_extractor import ParseError, extract_module, extract_modules

__all__ = [
    "ParseError",
    "extract_block_diagram",
    "extract_module",
    "extract_modules",
]
