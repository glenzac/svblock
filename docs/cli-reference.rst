CLI Reference
=============

Synopsis
--------

.. code-block:: text

   svblock [OPTIONS] INPUT_FILE [INPUT_FILE ...]

svblock reads one or more SystemVerilog / Verilog source files, extracts module
definitions, and renders pin diagrams.

Positional Arguments
--------------------

``INPUT_FILE``
    One or more ``.sv`` or ``.v`` files to process. Each file is rendered
    independently. When multiple files are given, svblock processes them in order
    and stops on the first error.

Options
-------

``-o``, ``--output PATH``
    Output file path. Defaults to ``<module_name>.<format>`` in the current
    directory.

    .. code-block:: bash

       svblock fifo.sv -o diagrams/fifo_diagram.svg

``-f``, ``--format {svg,png,pdf}``
    Output format. Default: ``svg``.

    PNG and PDF formats require ``cairosvg`` to be installed:

    .. code-block:: bash

       pip install svblock[png]
       svblock fifo.sv -f png

``-m``, ``--module TEXT``
    Name of the module to extract. By default, svblock renders the first module
    found in the file. Use ``--list-modules`` to discover available modules.

    .. code-block:: bash

       svblock top.sv -m uart_rx

``--theme NAME``
    Visual theme to apply. Can be a built-in theme name (``default``, ``dark``,
    ``minimal``, ``print``) or a path to a custom TOML/YAML theme file.

    .. code-block:: bash

       svblock fifo.sv --theme dark
       svblock fifo.sv --theme my_theme.toml

    See :doc:`themes` for details on built-in themes and creating custom ones.

``--no-params``
    Suppress the parameter section in the diagram header. Parameters are hidden
    but the module name is still displayed.

``--no-groups``
    Suppress group separator lines. All ports are rendered in a flat list without
    visual grouping.

``--no-decorators``
    Suppress pin decorators (clock triangles, active-low bubbles, bus thick
    strokes, interface diamonds). Pins are rendered as plain lines.

``--width INTEGER``
    Override the minimum box width in pixels. The layout engine normally
    auto-sizes the box based on label widths.

    .. code-block:: bash

       svblock fifo.sv --width 500

``--list-modules``
    List all module names found in the input file(s) and exit. Does not produce
    any diagram output.

    .. code-block:: bash

       $ svblock soc_top.sv --list-modules
       uart_tx
       uart_rx
       spi_master
       soc_top

``--block-diagram``
    Render a block diagram showing the module's internal structure -- child
    instances as boxes with directional arrows for connectivity. See
    :doc:`block-diagrams` for details.

    .. code-block:: bash

       svblock soc_top.sv --block-diagram -m soc_top

``--show-parent-ports``
    When used with ``--block-diagram``, display the parent module's I/O ports
    on the outer boundary with dashed lines to connected child instances.

    .. code-block:: bash

       svblock soc_top.sv --block-diagram --show-parent-ports -m soc_top

``--sphinx``
    Produce Sphinx-compatible SVG output (no ``xmlns`` attribute on the root
    ``<svg>`` element). Intended for use by the Sphinx extension internally.

``-v``, ``--verbose``
    Print parse diagnostics to stderr. Useful for debugging annotation parsing
    and port extraction.

``--version``
    Print the version number and exit.

Exit Codes
----------

.. list-table::
   :header-rows: 1
   :widths: 10 90

   * - Code
     - Meaning
   * - ``0``
     - Success
   * - ``1``
     - General error (file not found, invalid arguments, missing dependencies)
   * - ``2``
     - Parse error (no modules found, invalid SystemVerilog)

Examples
--------

Render with dark theme and custom output path:

.. code-block:: bash

   svblock alu.sv --theme dark -o docs/alu_pinout.svg

Batch render multiple files:

.. code-block:: bash

   svblock src/uart_tx.sv src/uart_rx.sv src/spi_master.sv

Minimal diagram with no extras:

.. code-block:: bash

   svblock fifo.sv --no-params --no-groups --no-decorators

Block diagram of a top-level module:

.. code-block:: bash

   svblock soc_top.sv --block-diagram -m soc_top --theme dark -o soc_block.svg
