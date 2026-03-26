svblock
=======

**A SystemVerilog-native module symbol (pin diagram) generator.**

svblock parses ``.sv`` / ``.v`` files using `pyslang <https://pypi.org/project/pyslang/>`_
(IEEE 1800-2017 compliant) and renders clean, CSS-themeable SVG pin diagrams.
Zero native dependencies -- no GTK, Cairo, or Pango required for SVG output.

.. raw:: html

   <div class="svblock-example">

.. image:: _static/examples/large_module.svg
   :alt: Example pin diagram of a large SystemVerilog module

.. raw:: html

   </div>

Features
--------

- Full **SystemVerilog 2017** support via ``pyslang`` -- ``logic``, packed arrays,
  interfaces, modports, parametric types
- **Comment-driven port grouping** (``// @sym group="Clocks"``) with automatic
  heuristic fallback
- **Pin decorators**: clock triangle, active-low bubble, bus thick stroke,
  interface diamond, inout arrow
- **4 built-in themes**: default, dark, minimal, print -- plus custom TOML/YAML themes
- **Deterministic SVG** output safe for version control and PR diffing
- Optional **PNG/PDF** export via ``cairosvg``
- **Sphinx extension** (``.. svblock::`` directive) for embedding diagrams in docs

.. toctree::
   :maxdepth: 2
   :caption: Contents

   getting-started
   cli-reference
   port-grouping
   themes
   examples
   sphinx-extension
   architecture
   api
   contributing
