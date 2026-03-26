Architecture
============

svblock uses a four-stage pipeline to transform SystemVerilog source files into
SVG pin diagrams.

.. code-block:: text

   .sv file --> Parse --> Module IR --> Layout --> SVG Render --> .svg file

Each stage is cleanly separated with well-defined data structures flowing
between them.

Pipeline Stages
---------------

Stage 1: Parser
~~~~~~~~~~~~~~~

**Module:** ``svblock.parser``

The parser stage uses `pyslang <https://pypi.org/project/pyslang/>`_ to build a
full IEEE 1800-2017 compliant syntax tree from the input file. It then walks the
tree to extract:

- Module name
- Port declarations (direction, type, bus range, name)
- Parameter declarations (type, name, default value)
- Source line numbers for annotation association

Additionally, the annotation sub-parser (``svblock.parser.annotation``) scans
the raw source text for ``// @sym`` comments and associates them with ports by
line proximity.

**Key design choice:** pyslang is the only parser backend. There is no fallback
to regex-based parsing or other tools. This ensures full SV 2017 compliance.

Stage 2: Module IR
~~~~~~~~~~~~~~~~~~

**Module:** ``svblock.model``

The intermediate representation consists of three dataclasses:

- ``PortDef`` -- a single port with direction, name, bus range (as strings),
  and decorator markers (clock, active-low, bus, interface)
- ``ParamDef`` -- a parameter with type, name, and default value
- ``ModuleIR`` -- the complete module with name, ports, parameters, and groups

Bus ranges are kept as strings (e.g., ``"WIDTH-1"``, ``"0"``) and are never
evaluated, since they may contain parametric expressions.

Stage 3: Layout
~~~~~~~~~~~~~~~

**Module:** ``svblock.layout``

The layout engine computes all geometric coordinates for the diagram:

- **Box sizing** -- based on the longest port labels, module name width, and
  parameter count
- **Pin placement** -- inputs on the left, outputs/inout/interfaces on the right
- **Group separators** -- dashed lines between port groups, with centered labels
- **Header** -- module name centered, parameters listed below

The layout stage also applies heuristic grouping when no annotations are present,
detecting common patterns like clock and reset signals.

Key configuration values (from ``LayoutConfig``):

.. list-table::
   :header-rows: 1
   :widths: 35 15 50

   * - Parameter
     - Default
     - Description
   * - ``pin_row_height``
     - 20px
     - Vertical space per pin
   * - ``min_box_width``
     - 240px
     - Minimum diagram width
   * - ``pin_stub_length``
     - 30px
     - Length of pin lines extending from the box
   * - ``header_base_height``
     - 36px
     - Height of the module name area
   * - ``header_param_line_height``
     - 16px
     - Additional height per parameter line

Stage 4: SVG Renderer
~~~~~~~~~~~~~~~~~~~~~~

**Module:** ``svblock.renderer``

The renderer translates the ``LayoutSpec`` into an SVG string using pure Python
string concatenation (no template engine). It generates:

- A ``<style>`` block with CSS custom properties from the active theme
- The main box ``<rect>`` and header
- Pin lines (``<line>``) with CSS class-based coloring
- Pin labels (``<text>``) with ``<title>`` tooltips
- Decorator shapes: ``<polygon>`` for clocks/diamonds, ``<circle>`` for
  active-low bubbles
- Group separator ``<line>`` elements with ``stroke-dasharray``

**Determinism guarantees:**

- Element IDs follow the pattern ``port-{name}``, ``group-{name}``,
  ``module-{name}``
- Ports are rendered in declaration order
- All floats are rounded to 2 decimal places
- No timestamps or random values in the output

This makes the SVG output safe for version control -- diffs will only show
meaningful changes.

Supporting Modules
------------------

Exporters
~~~~~~~~~

**Module:** ``svblock.exporters``

Optional PNG and PDF export via ``cairosvg``. These are thin wrappers that take
an SVG string and write the converted output to a file. The ``cairosvg``
dependency is lazy-imported, so it's only required when PNG/PDF output is
requested.

Sphinx Extension
~~~~~~~~~~~~~~~~

**Module:** ``svblock.sphinx_ext``

A Sphinx directive (``.. svblock::``) that runs the full pipeline at build time
and injects the SVG as a raw HTML node. See :doc:`sphinx-extension` for usage.

Configuration
~~~~~~~~~~~~~

**Module:** ``svblock.config``

Loads themes from built-in presets or custom TOML/YAML files. Custom values are
merged with the default theme so that partial overrides work correctly.

Directory Structure
-------------------

.. code-block:: text

   src/svblock/
   +-- __init__.py              # Package version
   +-- cli.py                   # CLI entry point
   +-- config.py                # Theme loading (TOML/YAML)
   +-- py.typed                 # PEP 561 marker
   +-- parser/
   |   +-- sv_extractor.py      # pyslang wrapper
   |   +-- annotation.py        # @sym comment parser
   +-- model/
   |   +-- port_types.py        # PortDirection enum
   |   +-- module_ir.py         # ModuleIR, PortDef, ParamDef
   +-- layout/
   |   +-- engine.py            # Box geometry & pin coordinates
   |   +-- grouping.py          # Heuristic & annotation grouping
   |   +-- text_metrics.py      # Font width estimation
   +-- renderer/
   |   +-- svg_renderer.py      # SVG string generation
   |   +-- themes.py            # Built-in theme definitions
   +-- exporters/
   |   +-- png.py               # cairosvg PNG wrapper
   |   +-- pdf.py               # cairosvg PDF wrapper
   +-- sphinx_ext/
       +-- directive.py          # Sphinx .. svblock:: directive
