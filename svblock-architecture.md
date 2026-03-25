# SVBLOCK — Architecture & Design Outline

> A modern, SystemVerilog-native module symbol generator. Inspired by Symbolator,
> built from scratch to solve the gaps it leaves behind.

---

## 1. Problem Statement

Documentation-quality pin diagrams for SystemVerilog modules do not have a maintained,
open-source solution. The closest tool — **Symbolator** — has the following critical
shortcomings that make it unsuitable as a foundation:

- Unmaintained (last commit 2018); broken on Python 3.10+ due to GTK/Pango bindings
- Verilog support limited to 1995/2001 syntax via `hdlparse` (a regex-based, non-standard parser)
- No SystemVerilog language support: no `logic`, no packed arrays, no interfaces, no modports
- No port-grouping annotations for Verilog (VHDL-only feature in Symbolator)
- Rendering locked to Cairo/Pango — heavy native dependencies, no CSS theming
- SVG output is not stable/diffable (not safe to commit to version control)

**Adjacent tools do not fill this gap:**

| Tool | What it does | Why it's not enough |
|---|---|---|
| Yosys | Post-synthesis netlist viewer | Shows gates, not RTL module interfaces |
| Verilator | Hierarchy + simulation | No pin diagram; full simulation overhead |
| Makerchip | Browser-based SV IDE | Full environment, not a CLI documentation tool |
| draw.io / Visio | Manual diagramming | No HDL parsing; manual maintenance burden |
| Graphviz + Verilog-Perl | Hierarchy/connectivity graphs | Not a symbol/pin diagram generator |

---

## 2. Goals

### Primary goals
- Parse any real-world SystemVerilog (IEEE 1800-2017) module and render a clean pin diagram
- Zero native dependencies (`pip install` just works — no GTK, Cairo, or Pango)
- SVG output by default; PNG/PDF as secondary targets
- Comment-driven port grouping for Verilog/SystemVerilog files
- CSS-themeable output (dark mode, custom palettes, documentation pipeline integration)

### Secondary goals
- Sphinx extension (drop-in `.. svblock::` directive)
- Stable, deterministic SVG output safe for version control and PR diffing
- Interface and modport port rendering as a distinct visual type
- YAML/TOML-based style configuration

### Out of scope (v1)
- VHDL support
- Netlist / post-synthesis diagrams
- Waveform or timing diagram generation
- Full module hierarchy / block diagrams (possible v2)

---

## 3. Technology Choices

### 3.1 Parser — `pyslang` (slang Python bindings)

**Decision: Use `pyslang` as the sole parser backend.**

- `slang` is the fastest and most spec-compliant SystemVerilog frontend available
  in open source (verified against the chipsalliance test suite)
- Fully parses, type-checks, and elaborates IEEE 1800-2017 SystemVerilog
- `pyslang` exposes the full AST and CST (concrete syntax tree, which preserves
  comments) to Python
- Handles everything `hdlparse` cannot: ANSI-style headers, `logic` type,
  packed/unpacked arrays, parameterized types, `include` resolution, `` `define ``
  macros, interfaces, modports
- MIT licensed; pip-installable

**Alternative parsers considered:**

| Library | Notes | Verdict |
|---|---|---|
| `hdlparse` | Regex-based; Verilog 2001 only | Insufficient for SV |
| `pyverilog` | Full Verilog AST; no SV | Fallback only |
| `pysvinst` | Rust-backed sv-parser; SV 2017 | Narrower scope; backup option |
| `hdlConvertor` | ANTLR4-based; SV 2017 | More complex build; secondary option |

### 3.2 Renderer — Pure Python SVG

**Decision: Generate SVG directly as Python strings/templates. No Cairo, no Pango.**

- Eliminates the GTK/Pango dependency that makes Symbolator uninstallable
- SVG is the primary output format; everything else (PNG, PDF) is derived via
  alternate tools like svglib or ImageMagick. 
- Text measurement (needed for dynamic box sizing) handled by a pre-computed
  character-width table for the chosen output font, or via `fonttools` (optional)

### 3.3 Language
- Python 3.10+
- No mandatory native dependencies beyond `pyslang`
- Optional: `svglib` or `ImageMagick` (PNG/PDF export), `Sphinx` (directive), `fonttools` (precise text metrics)

---

## 4. Architecture

### 4.1 Pipeline Overview

```
.sv / .v file
      │
      ▼
┌─────────────────────────────────────┐
│  Stage 1: Parse  (pyslang)          │
│  – Full SV 2017 parse               │
│  – Extract ports, params, comments  │
│  – Resolve interfaces / modports    │
└──────────────┬──────────────────────┘
               │
      ┌────────▼────────┐
      │  Comment        │
      │  annotations    │  (// @sym group=Clocks)
      └────────┬────────┘
               │
┌──────────────▼──────────────────────┐
│  Stage 2: Module IR                 │
│  – Normalized port / param model    │
│  – Group assignments                │
│  – Type annotations (bus, iface…)  │
└──────────────┬──────────────────────┘
               │
      ┌────────▼────────┐
      │  Style config   │
      │  (YAML / CSS)   │
      └────────┬────────┘
               │
┌──────────────▼──────────────────────┐
│  Stage 3: Layout engine             │
│  – Box sizing from port list        │
│  – Pin row layout (left/right)      │
│  – Group separators                 │
│  – Bus / interface indicators       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Stage 4: SVG Renderer              │
│  – Pure Python string generation    │
│  – CSS variable injection           │
│  – Stable, deterministic output     │
└──────────────┬──────────────────────┘
               │
      ┌────────▼──────────────┐
      │  Outputs              │
      │  SVG (default)        │
      │  PNG / PDF (optional) │
      │  Sphinx directive     │
      └───────────────────────┘
```

### 4.2 Module Breakdown

```
svblock/
├── cli.py                  # Argument parsing, entry point
├── parser/
│   ├── __init__.py
│   ├── sv_extractor.py     # pyslang wrapper: extracts ModuleIR from .sv/.v
│   └── annotation.py       # Parses // @sym comment annotations from CST
├── model/
│   ├── __init__.py
│   ├── module_ir.py        # ModuleIR, PortDef, ParamDef, GroupDef dataclasses
│   └── port_types.py       # Enum: INPUT, OUTPUT, INOUT, INTERFACE, MODPORT
├── layout/
│   ├── __init__.py
│   ├── engine.py           # Computes box geometry, pin coordinates
│   ├── text_metrics.py     # Character width table / fonttools integration
│   └── grouping.py         # Assigns ports to groups, orders sections
├── renderer/
│   ├── __init__.py
│   ├── svg_renderer.py     # Generates SVG string from layout spec
│   ├── themes.py           # Built-in themes (default, dark, minimal)
│   └── templates/
│       └── base.svg.jinja  # Optional: Jinja2 template for SVG skeleton
├── exporters/
│   ├── __init__.py
│   ├── png.py              # svg to png wrapper (optional dep)
│   └── pdf.py              # svg to pdf wrapper (optional dep)
├── sphinx_ext/
│   ├── __init__.py
│   └── directive.py        # .. svblock:: Sphinx directive
└── config.py               # Loads YAML / TOML style config
```

---

## 5. Data Model

### 5.1 `PortDef`

```python
@dataclass
class PortDef:
    name: str
    direction: PortDirection          # INPUT | OUTPUT | INOUT | INTERFACE | REF
    port_type: str                    # Raw SV type string: "logic", "logic [7:0]", etc.
    is_bus: bool                      # True if packed array
    bus_range: tuple[str, str] | None # ("WIDTH-1", "0") — kept as strings (param-safe)
    is_interface: bool
    modport: str | None               # e.g. "master", "slave"
    group: str | None                 # Assigned by @sym annotation or heuristic
    has_clock_marker: bool            # Pin name matches clk/clock pattern
    has_active_low_marker: bool       # Pin name ends in _n / _b / _N
```

### 5.2 `ParamDef`

```python
@dataclass
class ParamDef:
    name: str
    param_type: str                   # "integer", "bit", custom typedef, etc.
    default_value: str | None
    is_localparam: bool
```

### 5.3 `ModuleIR`

```python
@dataclass
class ModuleIR:
    name: str
    file_path: str
    ports: list[PortDef]
    params: list[ParamDef]
    groups: list[GroupDef]            # Ordered; ungrouped ports get a default group
```

---

## 6. Comment Annotation System

Port grouping is the most user-visible feature missing from Symbolator's Verilog support.
The annotation system uses structured comments directly above a port or port block.

### Syntax

```systemverilog
module my_dut #(
    parameter int WIDTH = 8
)(
    // @sym group="Clocks"
    input  logic        clk,
    input  logic        rst_n,

    // @sym group="Data In"
    input  logic [WIDTH-1:0] data_in,
    input  logic             valid_in,

    // @sym group="Data Out"
    output logic [WIDTH-1:0] data_out,
    output logic             valid_out,

    // @sym group="Interface" label="AXI Master"
    axi_if.master            axi
);
```

### Supported annotation keys (v1)

| Key | Description |
|---|---|
| `group` | Section name for grouping ports visually |
| `label` | Override the displayed port name |
| `hide`  | Exclude this port from the diagram |
| `bus`   | Force bus rendering even for scalar ports |
| `color` | Override pin color in the output SVG |

### Heuristic fallback (no annotations)

When no `@sym` annotations are present, the tool applies heuristics:
- Ports matching `clk`, `clock`, `*_clk` → group "Clocks"
- Ports matching `rst*`, `reset*` → group "Resets"
- Remaining inputs → group "Inputs"
- Remaining outputs → group "Outputs"
- Interface/modport ports → group "Interfaces"

---

## 7. Layout Engine

### 7.1 Box geometry rules

- **Pin row height:** 20px per pin; 28px for interface pins (slightly taller)
- **Group header height:** 18px per group separator
- **Box width:** `max(max_input_label_width, max_output_label_width) × 2 + module_name_width + padding`
- **Minimum box width:** 240px
- **Header height (module name + params):** 36px base + 16px per parameter line
- **Padding:** 12px inside box edges, 8px between pin label and box edge

### 7.2 Pin placement rules

- Inputs always on the left side
- Outputs always on the right side
- Bidirectional (`inout`) on the right side, marked with a double-arrow indicator
- Interface ports on the right side, marked with a distinct connector symbol
- Pins within each group maintain source-file declaration order
- Group separators are thin horizontal rules with a centered group name label

### 7.3 Pin decorators

| Condition | Decorator |
|---|---|
| Port name matches `clk*`, `*_clk` | Edge-sensitive triangle (▷) |
| Port name ends in `_n`, `_b`, `_N` | Inversion bubble (○) |
| `is_bus == True` | Bus stroke (thick pin line) + `[H:L]` label |
| `is_interface == True` | Filled diamond connector |
| `direction == INOUT` | Double-headed arrow (↔) |

---

## 8. SVG Renderer

### 8.1 Output structure

```xml
<svg xmlns="http://www.w3.org/2000/svg" width="W" height="H"
     viewBox="0 0 W H" class="svblock">
  <style>
    /* CSS variables for theming */
    :root {
      --sym-bg:           #ffffff;
      --sym-border:       #333333;
      --sym-text:         #111111;
      --sym-pin-input:    #1a6db5;
      --sym-pin-output:   #b52a1a;
      --sym-pin-inout:    #6a2ab5;
      --sym-pin-iface:    #1a9e55;
      --sym-group-bg:     #f0f0f0;
      --sym-group-text:   #555555;
      --sym-bus-stroke:   3px;
    }
  </style>
  <!-- Module box -->
  <!-- Header: module name -->
  <!-- Parameter section (if params present) -->
  <!-- Port rows (left: inputs, right: outputs) -->
  <!-- Group separators -->
</svg>
```

### 8.2 Theming

Themes are YAML files mapping CSS variable names to values.

Built-in themes: `default` (light), `dark`, `minimal` (monochrome), `print` (high contrast B&W).

Custom themes can be supplied via `--theme path/to/theme.yaml`.

### 8.3 Stability guarantees for VCS use

- Ports are rendered in declaration order (not alphabetically sorted)
- No timestamps or build metadata embedded in SVG
- Deterministic element IDs: `port-{name}`, `group-{name}`, `param-{name}`
- Floating point coordinates rounded to 2 decimal places

---

## 9. CLI Interface

```
Usage: svblock [OPTIONS] INPUT_FILE [INPUT_FILE ...]

Options:
  -o, --output PATH         Output file path (default: <module>.<format>)
  -f, --format [svg|png|pdf|eps]
                            Output format (default: svg)
  -m, --module TEXT         Module name to extract (default: first module found)
  --theme [default|dark|minimal|print|PATH]
                            Visual theme (default: default)
  --no-params               Suppress parameter section
  --no-groups               Suppress group separators (flat port list)
  --no-decorators           Suppress clock/active-low/bus decorators
  --width INTEGER           Override minimum box width in pixels
  --list-modules            List all modules found in the file and exit
  --sphinx                  Output Sphinx-compatible SVG (standalone=false)
  -v, --verbose             Show parse diagnostics
  --version                 Show version and exit
```

**Examples:**

```bash
# Basic usage — renders first module found as SVG
svblock my_module.sv

# Specific module, dark theme, PNG output
svblock my_module.sv -m fifo_ctrl --theme dark -f png

# Batch: render all modules in a file
svblock my_module.sv --list-modules | xargs -I{} svblock my_module.sv -m {}

# Used in a Makefile
docs/%.svg: rtl/%.sv
    svblock $< -o $@
```

---

## 10. Sphinx Extension

```rst
.. svblock:: path/to/my_module.sv
   :module: fifo_ctrl
   :theme: default
   :caption: FIFO Controller interface
   :align: center
   :no-params:
```

The directive calls the renderer directly (no subprocess) and embeds the SVG inline
or as a linked image depending on the Sphinx builder (HTML vs LaTeX).

Configuration in `conf.py`:

```python
extensions = ['svblock.sphinx_ext']

svblock_default_theme = 'dark'
svblock_include_paths = ['../rtl', '../ip']  # for `include resolution
svblock_default_format = 'svg'
```

---

## 11. SystemVerilog-Specific Rendering Details

These are the features that differentiate this tool from anything Symbolator can do.

### 11.1 Interface ports

```systemverilog
axi_if.master   axi_m,    // rendered as: ◆ axi_m [AXI master]
axi_if.slave    axi_s,    // rendered as: ◆ axi_s [AXI slave]
```

- Interface ports get a filled-diamond symbol (◆)
- Modport name displayed in brackets as a secondary label
- Color-coded distinctly from scalar/vector ports

### 11.2 Packed array types

```systemverilog
input  logic [WIDTH-1:0]    data,    // bus with parametric range
input  logic [3:0][7:0]     matrix,  // multi-dimensional: shown as "4×8"
```

- Parametric ranges are preserved as strings (`WIDTH-1 : 0`), not evaluated
- Multi-dimensional arrays show a compact notation

### 11.3 Parameter types

```systemverilog
parameter int           WIDTH   = 8,
parameter type          T       = logic,    // type parameter
parameter string        NAME    = "default"
```

- Type parameters (`parameter type`) rendered with a distinct marker
- String parameters truncated to 16 chars with `…` in the diagram

### 11.4 `logic` vs `wire` vs `reg`

- No visual distinction made between `logic`, `wire`, `reg` in v1 — all rendered as
  standard pins. The type string is displayed as a secondary label on hover in SVG
  (via `<title>` element) but not in the main diagram to avoid clutter.

---

## 12. Build & Effort Estimate

| Component | Effort | Notes |
|---|---|---|
| `pyslang` integration + port extraction | 2–3 days | Core happy path is straightforward |
| Comment annotation parser | 2–3 days | Walks CST for trivia/comments |
| `ModuleIR` data model | 1 day | Dataclasses, straightforward |
| Layout engine (geometry) | 3–5 days | Text measurement is the tricky part |
| SVG renderer + theming | 4–6 days | Mostly mechanical; theme system adds time |
| CLI + config loader | 2 days | argparse / click |
| Interface/modport rendering | 3–5 days | Most SV-specific design work |
| PNG/PDF export | 1 day | Thin wrapper over cairosvg |
| Sphinx extension | 2 days | Derived from Graphviz extension pattern |
| Tests + CI | 3–5 days | Snapshot tests for SVG output |
| **MVP total** | **~3 weeks** | Handles 90% of real-world SV modules |
| **Full v1 total** | **~6–8 weeks** | All features + docs + packaging |

---

## 13. Testing Strategy

### Snapshot tests
- Render a curated library of representative `.sv` files; commit the SVG outputs
- Any rendering change produces a diff, which must be intentionally approved
- Test modules should cover: simple ports, buses, interfaces, parameters, groups,
  active-low signals, clock ports, multi-module files, ANSI and non-ANSI headers

### Parser robustness tests
- Feed intentionally malformed or partial SV; verify graceful error messages
- Test against real open-source SV (e.g. OpenTitan, CVA6 RTL modules)

### CLI tests
- Invocation with each flag combination
- Batch rendering
- `--list-modules` on multi-module files

---

## 14. Future Work (Post v1)

- **Hierarchy diagrams:** Given a top-level module and its includes, render a
  block diagram showing submodule connectivity (leverages pyslang elaboration)
- **Diff mode:** Given two versions of a `.sv` file, render the symbol with
  added/removed/changed ports highlighted
- **VS Code extension:** On-the-fly symbol preview in the editor sidebar
- **Wavedrom integration:** Annotate ports with protocol timing diagrams
- **Web UI:** Browser-based renderer (pyslang → Wasm is on the slang roadmap)

---

## 15. References

| Resource | URL |
|---|---|
| Symbolator (original) | https://github.com/kevinpt/symbolator |
| hdl/symbolator (community fork) | https://github.com/hdl/symbolator |
| slang SystemVerilog compiler | https://github.com/MikePopoloski/slang |
| pyslang Python bindings | https://pypi.org/project/pyslang/ |
| pyverilog | https://pypi.org/project/pyverilog/ |
| pysvinst (sv-parser Rust backend) | https://github.com/sgherbst/pysvinst |
| hdlConvertor (ANTLR4-based) | https://github.com/Nic30/hdlConvertor |
| IEEE 1800-2017 (SystemVerilog LRM) | https://ieeexplore.ieee.org/document/8299595 |
