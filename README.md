# svblock

A SystemVerilog-native module symbol (pin diagram) generator.

Parses `.sv`/`.v` files using [pyslang](https://pypi.org/project/pyslang/) (IEEE 1800-2017) and renders clean, CSS-themeable SVG pin diagrams with zero native dependencies.

## Installation

```bash
pip install svblock
```

## Quick Start

```bash
# Render the first module found as SVG
svblock my_module.sv

# Specific module, dark theme, PNG output
svblock my_module.sv -m fifo_ctrl --theme dark -f png

# List all modules in a file
svblock my_module.sv --list-modules
```

See [svblock-architecture.md](svblock-architecture.md) for the full design document.
