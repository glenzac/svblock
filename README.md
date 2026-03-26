# svblock

A SystemVerilog-native module symbol (pin diagram) generator.

Parses `.sv`/`.v` files using [pyslang](https://pypi.org/project/pyslang/) (IEEE 1800-2017) and renders clean, CSS-themeable SVG pin diagrams with zero native dependencies.

## Features

- Full **SystemVerilog 2017** support via `pyslang` — `logic`, packed arrays, interfaces, modports, parametric types
- **Comment-driven port grouping** (`// @sym group="Clocks"`) with automatic heuristic fallback
- **Pin decorators**: clock triangle, active-low bubble, bus thick stroke, interface diamond, inout arrow
- **4 built-in themes**: default, dark, minimal, print — plus custom TOML/YAML themes
- **Deterministic SVG** output safe for version control and PR diffing
- Optional **PNG/PDF** export via `cairosvg`
- **Sphinx extension** (`.. svblock::` directive)

## Installation

```bash
pip install svblock

# With optional export support
pip install svblock[png]    # PNG export
pip install svblock[pdf]    # PDF export
pip install svblock[sphinx] # Sphinx directive
```

## Quick Start

```bash
# Render the first module found as SVG
svblock my_module.sv

# Specific module, dark theme
svblock my_module.sv -m fifo_ctrl --theme dark

# PNG output (requires cairosvg)
svblock my_module.sv -f png

# List all modules in a file
svblock my_module.sv --list-modules
```

## CLI Options

```
svblock [OPTIONS] INPUT_FILE [INPUT_FILE ...]

  -o, --output PATH       Output file path (default: <module>.<format>)
  -f, --format {svg,png,pdf}  Output format (default: svg)
  -m, --module TEXT        Module name to extract (default: first found)
  --theme NAME             Theme: default, dark, minimal, print, or path to TOML/YAML
  --no-params              Suppress parameter section
  --no-groups              Suppress group separators (flat port list)
  --no-decorators          Suppress clock/active-low/bus decorators
  --width INTEGER          Override minimum box width in pixels
  --list-modules           List all modules and exit
  --sphinx                 Output Sphinx-compatible SVG (no xmlns)
  -v, --verbose            Show parse diagnostics
  --version                Show version and exit
```

## Port Grouping

### Annotation-driven

Add `// @sym` comments in your module to control grouping and visibility:

```systemverilog
module my_fifo (
    // @sym group="Clocks"
    input  logic       clk,
    input  logic       rst_n,

    // @sym group="Write Port"
    input  logic [7:0] wr_data,
    input  logic       wr_en,

    // @sym group="Read Port"
    output logic [7:0] rd_data,
    output logic       rd_en,

    // @sym hide=true
    output logic       debug_out
);
endmodule
```

### Heuristic grouping

When no annotations are present, svblock automatically groups ports by pattern:
- **Clocks**: `clk`, `clock`, `*_clk`, `*_clock`
- **Resets**: `rst*`, `reset*`
- Remaining ports grouped by direction (Inputs, Outputs, Interfaces)

## Sphinx Integration

Add `svblock.sphinx_ext` to your Sphinx `conf.py` extensions:

```python
extensions = [
    "svblock.sphinx_ext",
]
```

Then use the directive in your `.rst` files:

```rst
.. svblock:: path/to/module.sv
   :module: fifo_ctrl
   :theme: dark
   :no-params:
   :width: 400
```

## Themes

Four built-in themes are available. Custom themes can be defined in TOML or YAML files that override CSS variables:

```toml
# my_theme.toml
[theme]
"--sym-bg" = "#f5f5dc"
"--sym-border" = "#8b4513"
"--sym-pin-input" = "#006400"
"--sym-pin-output" = "#8b0000"
```

```bash
svblock module.sv --theme my_theme.toml
```

## Development

```bash
# Install in development mode
pip install -e ".[dev,sphinx]"

# Run tests (174 tests)
pytest

# Lint
ruff check src/ tests/

# Regenerate golden SVG snapshots
python tests/update_snapshots.py
```

## Architecture

Four-stage pipeline: **Parse -> Module IR -> Layout -> SVG Render**

1. **Parser** (`svblock/parser/`) — `pyslang` wrapper extracts ports, params, and `@sym` annotations
2. **Model** (`svblock/model/`) — `ModuleIR`, `PortDef`, `ParamDef` dataclasses
3. **Layout** (`svblock/layout/`) — box geometry, pin coordinates, group separators
4. **Renderer** (`svblock/renderer/`) — pure Python SVG string generation with CSS theming

## License

MIT
