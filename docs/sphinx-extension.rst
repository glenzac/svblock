Sphinx Extension
================

svblock includes a Sphinx extension that provides the ``.. svblock::`` directive
for embedding pin diagrams directly in your documentation.

Setup
-----

Install svblock with Sphinx support:

.. code-block:: bash

   pip install svblock[sphinx]

Add the extension to your Sphinx ``conf.py``:

.. code-block:: python

   extensions = [
       "svblock.sphinx_ext",
       # ... other extensions
   ]

Basic Usage
-----------

The directive takes a path to a SystemVerilog file (relative to the Sphinx
source directory) and renders the module as an inline SVG:

.. code-block:: rst

   .. svblock:: hdl/fifo.sv

This renders the first module found in the file.

Directive Options
-----------------

.. code-block:: rst

   .. svblock:: hdl/fifo.sv
      :module: fifo_ctrl
      :theme: dark
      :no-params:
      :no-groups:
      :no-decorators:
      :width: 400

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Option
     - Type
     - Description
   * - ``:module:``
     - string
     - Name of the module to render. Defaults to the first module in the file.
   * - ``:theme:``
     - string
     - Theme name (``default``, ``dark``, ``minimal``, ``print``) or path to a
       custom TOML/YAML theme file.
   * - ``:no-params:``
     - flag
     - Suppress the parameter section in the header.
   * - ``:no-groups:``
     - flag
     - Suppress group separator lines.
   * - ``:no-decorators:``
     - flag
     - Suppress clock/active-low/bus decorators.
   * - ``:width:``
     - integer
     - Override minimum box width in pixels.

Examples
--------

**Minimal:**

.. code-block:: rst

   .. svblock:: hdl/uart_tx.sv

**Specific module with dark theme:**

.. code-block:: rst

   .. svblock:: hdl/soc_top.sv
      :module: spi_master
      :theme: dark

**Clean diagram for a datasheet:**

.. code-block:: rst

   .. svblock:: hdl/adc_controller.sv
      :no-params:
      :no-decorators:
      :theme: print
      :width: 500

Error Handling
--------------

The directive reports Sphinx warnings (not build failures) for:

- File not found
- No modules found in the file
- Parse errors in the SystemVerilog source

This means a broken ``.sv`` path won't break your entire docs build -- it will
produce a warning and skip the diagram.

How It Works
------------

The directive runs the full svblock pipeline at Sphinx build time:

1. Resolves the ``.sv`` file path relative to the Sphinx source directory
2. Parses the file with ``pyslang``
3. Applies grouping, layout, and rendering
4. Injects the resulting SVG as a raw HTML node in the document

Since ``pyslang`` is required at build time, ensure it is installed in your docs
build environment.
