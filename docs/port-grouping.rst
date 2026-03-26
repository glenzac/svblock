Port Grouping
=============

svblock groups ports into labeled sections within the pin diagram. Grouping can
be controlled explicitly with comment annotations or applied automatically
using heuristic pattern matching.

Annotation-Driven Grouping
--------------------------

Add ``// @sym`` comments in your SystemVerilog source to control how ports are
grouped and displayed.

Group Assignment
~~~~~~~~~~~~~~~~

The ``group`` attribute assigns subsequent ports to a named group:

.. code-block:: systemverilog

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

This produces the following diagram:

.. raw:: html

   <div class="svblock-example">

.. image:: _static/examples/annotated.svg
   :alt: Annotated module with explicit port groups

.. raw:: html

   </div>

Annotation Syntax
~~~~~~~~~~~~~~~~~

Annotations use the format ``// @sym key="value" [key="value" ...]``:

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Key
     - Values
     - Effect
   * - ``group``
     - Any string
     - Assigns following ports to the named group
   * - ``hide``
     - ``true`` / ``false``
     - Hides the port from the diagram

**Scope rules:**

- A ``group`` annotation applies to all ports that follow it, until the next
  ``group`` annotation or a blank line.
- A ``hide`` annotation applies to the immediately following port(s) until the
  next annotation.
- Annotations are associated with ports by source line proximity -- they must
  appear directly above the port declarations they affect.

Heuristic Grouping
------------------

When no ``// @sym`` annotations are present, svblock automatically groups ports
by matching their names against common patterns:

.. list-table::
   :header-rows: 1
   :widths: 25 40 35

   * - Group
     - Patterns
     - Examples
   * - **Clocks**
     - ``clk``, ``clock``, ``*_clk``, ``*_clock``
     - ``clk``, ``sys_clk``, ``ref_clock``
   * - **Resets**
     - ``rst*``, ``reset*``
     - ``rst_n``, ``reset``, ``rst_async``
   * - **Inputs**
     - Remaining input ports
     - ``data_in``, ``enable``, ``addr``
   * - **Outputs**
     - Remaining output ports
     - ``data_out``, ``valid``, ``ready``
   * - **Interfaces**
     - Interface/modport ports
     - ``axi_m``, ``axi_s``

Example with heuristic grouping (no annotations):

.. code-block:: systemverilog

   module clock_reset (
       input  logic clk,
       input  logic sys_clk,
       input  logic rst_n,
       input  logic reset,
       input  logic data_in,
       output logic data_out
   );
   endmodule

.. raw:: html

   <div class="svblock-example">

.. image:: _static/examples/clock_reset.svg
   :alt: Module with heuristic clock/reset grouping

.. raw:: html

   </div>

The clocks and resets are automatically detected and separated into their own
groups.

Disabling Grouping
------------------

To render a flat list of ports without any group separators, use the
``--no-groups`` CLI flag:

.. code-block:: bash

   svblock module.sv --no-groups

Or in the Sphinx directive:

.. code-block:: rst

   .. svblock:: module.sv
      :no-groups:
