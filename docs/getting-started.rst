Getting Started
===============

Installation
------------

Install svblock from PyPI:

.. code-block:: bash

   pip install svblock

Optional extras for export and documentation support:

.. code-block:: bash

   pip install svblock[png]     # PNG export (requires cairosvg)
   pip install svblock[pdf]     # PDF export (requires cairosvg)
   pip install svblock[sphinx]  # Sphinx directive support

Requirements
~~~~~~~~~~~~

- **Python 3.10+**
- **pyslang >= 6.0** (installed automatically)

Quick Start
-----------

Given a SystemVerilog file ``fifo.sv``:

.. code-block:: systemverilog

   module fifo #(
       parameter int DEPTH = 16,
       parameter int WIDTH = 8
   )(
       input  logic             clk,
       input  logic             rst_n,

       input  logic [WIDTH-1:0] wr_data,
       input  logic             wr_en,
       output logic             wr_full,

       output logic [WIDTH-1:0] rd_data,
       input  logic             rd_en,
       output logic             rd_empty
   );
   endmodule

Generate an SVG pin diagram:

.. code-block:: bash

   svblock fifo.sv

This produces ``fifo.svg`` in the current directory.

Common Workflows
~~~~~~~~~~~~~~~~

**Render a specific module** from a multi-module file:

.. code-block:: bash

   svblock top.sv -m uart_tx

**Use a dark theme:**

.. code-block:: bash

   svblock fifo.sv --theme dark

**Export as PNG** (requires ``cairosvg``):

.. code-block:: bash

   svblock fifo.sv -f png

**List all modules** in a file:

.. code-block:: bash

   svblock top.sv --list-modules

**Suppress parameters and decorators** for a minimal diagram:

.. code-block:: bash

   svblock fifo.sv --no-params --no-decorators

Development Installation
------------------------

Clone the repository and install in editable mode with development dependencies:

.. code-block:: bash

   git clone https://github.com/glenzac/svblock.git
   cd svblock
   pip install -e ".[dev,sphinx]"

Run the tests:

.. code-block:: bash

   pytest               # all 174 tests
   ruff check src/      # lint
