"""SystemVerilog parsing and annotation extraction."""

from __future__ import annotations

from svblock.parser.sv_extractor import ParseError, extract_module, extract_modules

__all__ = [
    "ParseError",
    "extract_module",
    "extract_modules",
]
