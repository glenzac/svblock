API Reference
=============

svblock can be used as a Python library in addition to the CLI. This page
documents the public API.

Data Model
----------

.. automodule:: svblock.model.port_types
   :members:
   :undoc-members:

.. automodule:: svblock.model.module_ir
   :members:
   :undoc-members:

Parser
------

.. automodule:: svblock.parser
   :members:
   :undoc-members:

.. automodule:: svblock.parser.annotation
   :members:

Layout
------

.. automodule:: svblock.layout.engine
   :members:
   :undoc-members:

.. automodule:: svblock.layout.grouping
   :members:

.. automodule:: svblock.layout.text_metrics
   :members:

Renderer
--------

.. automodule:: svblock.renderer.svg_renderer
   :members:

.. automodule:: svblock.renderer.themes
   :members:
   :undoc-members:

Configuration
-------------

.. automodule:: svblock.config
   :members:

Exporters
---------

.. automodule:: svblock.exporters.png
   :members:

.. automodule:: svblock.exporters.pdf
   :members:

Programmatic Usage
------------------

Here is a complete example of using svblock as a library:

.. code-block:: python

   from pathlib import Path

   from svblock.parser import extract_modules
   from svblock.layout.grouping import apply_grouping
   from svblock.layout.engine import LayoutConfig, compute_layout
   from svblock.renderer.svg_renderer import RenderOptions, render_svg
   from svblock.renderer.themes import BUILTIN_THEMES

   # Parse a SystemVerilog file
   modules = extract_modules(Path("fifo.sv"))
   module = modules[0]

   # Apply automatic grouping
   module = apply_grouping(module)

   # Compute layout
   config = LayoutConfig()
   layout = compute_layout(module, config)

   # Render SVG with dark theme
   theme = BUILTIN_THEMES["dark"]
   options = RenderOptions(standalone=True)
   svg_string = render_svg(layout, theme, options)

   # Write to file
   Path("fifo.svg").write_text(svg_string, encoding="utf-8")
