# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**svblock** is a SystemVerilog-native module symbol (pin diagram) generator. It parses `.sv`/`.v` files using `pyslang` (IEEE 1800-2017 compliant) and renders clean, CSS-themeable SVG pin diagrams. Zero native dependencies — no GTK, Cairo, or Pango.

## Build & Run Commands

```bash
# Install in development mode
pip install -e ".[dev]"

# CLI entry point
svblock INPUT_FILE.sv                          # render first module as SVG
svblock INPUT_FILE.sv -m module_name           # specific module
svblock INPUT_FILE.sv --theme dark -f png      # dark theme, PNG output (requires cairosvg)
svblock INPUT_FILE.sv --list-modules           # list all modules in file

# Tests
pytest                                         # all 174 tests
pytest tests/test_parser.py -k test_name       # single test
pytest tests/test_e2e.py                       # E2E snapshot tests

# Lint
ruff check src/ tests/

# Regenerate golden SVG snapshots
python tests/update_snapshots.py
```

## Architecture

Four-stage pipeline: **Parse → Module IR → Layout → SVG Render**

1. **Parser** (`svblock/parser/`): `pyslang` wrapper extracts ports, params, and `// @sym` comment annotations from the CST
2. **Model** (`svblock/model/`): `ModuleIR`, `PortDef`, `ParamDef` dataclasses — the normalized intermediate representation
3. **Layout** (`svblock/layout/`): Computes box geometry, pin coordinates, group separators. Inputs on left, outputs on right
4. **Renderer** (`svblock/renderer/`): Pure Python SVG string generation with CSS variable theming

Supporting modules:
- `svblock/exporters/` — PNG/PDF wrappers (optional dep: `cairosvg`)
- `svblock/sphinx_ext/` — `.. svblock::` Sphinx directive
- `svblock/config.py` — YAML/TOML style configuration loader

## Key Design Decisions

- **Parser**: `pyslang` only — no fallback to `hdlparse`/`pyverilog`. Full SV 2017 support required.
- **SVG output must be deterministic**: declaration-order rendering, no timestamps, deterministic element IDs (`port-{name}`, `group-{name}`), floats rounded to 2 decimal places. SVGs must be safe to commit and diff.
- **Comment annotations** (`// @sym group="Clocks"`) drive port grouping. When absent, heuristic grouping applies (clk→Clocks, rst→Resets, etc.).
- **Pin decorators**: clock triangle (▷), active-low bubble (○), bus thick stroke, interface diamond (◆), inout double-arrow (↔).
- **Bus ranges kept as strings** (e.g., `"WIDTH-1"`, `"0"`) — never evaluated, since they may be parametric.

## Tech Stack

- Python 3.10+
- `pyslang` — SystemVerilog parsing
- Optional: `cairosvg` (PNG/PDF export), `Sphinx` (docs directive)

## Testing

- **Snapshot tests**: render curated `.sv` files, commit SVG outputs, diff on changes
- **Parser robustness**: malformed/partial SV must produce graceful errors
- **CLI tests**: all flag combinations, batch rendering, `--list-modules`
- Test against real open-source SV (OpenTitan, CVA6) for parser coverage
