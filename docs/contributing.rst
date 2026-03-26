Contributing
============

Development Setup
-----------------

Clone the repository and install in editable mode:

.. code-block:: bash

   git clone https://github.com/glenzac/svblock.git
   cd svblock
   pip install -e ".[dev,sphinx]"

Running Tests
-------------

The test suite includes 174 tests covering the parser, model, layout, renderer,
CLI, themes, and end-to-end snapshot tests.

.. code-block:: bash

   # Run all tests
   pytest

   # Run a specific test file
   pytest tests/test_parser.py

   # Run a single test by name
   pytest tests/test_parser.py -k test_simple_module

   # Run with verbose output
   pytest -v

Linting
-------

The project uses `ruff <https://docs.astral.sh/ruff/>`_ for linting:

.. code-block:: bash

   ruff check src/ tests/

Type Checking
-------------

Type hints are enforced with ``mypy``:

.. code-block:: bash

   mypy src/svblock/ --ignore-missing-imports

Snapshot Tests
--------------

End-to-end tests compare rendered SVG output against golden reference files in
``tests/snapshots/``. If you make changes to the renderer or layout engine that
intentionally change the output:

1. Run the snapshot update script:

   .. code-block:: bash

      python tests/update_snapshots.py

2. Review the diffs in ``tests/snapshots/`` to verify the changes are correct.

3. Commit the updated snapshots with your code changes.

Test Fixtures
-------------

Test fixtures are ``.sv`` files in ``tests/fixtures/`` that cover a range of
SystemVerilog patterns:

- ``simple_module.sv`` -- minimal 3-port module
- ``annotated_module.sv`` -- explicit ``@sym`` group annotations
- ``bus_ports.sv`` -- parametric bus widths
- ``clock_reset.sv`` -- heuristic clock/reset detection
- ``active_low.sv`` -- active-low signal detection
- ``interface_ports.sv`` -- interfaces with modports
- ``large_module.sv`` -- complex multi-group module
- ``params.sv`` -- various parameter types
- ``multidim_array.sv`` -- multi-dimensional arrays
- ``non_ansi.sv`` -- non-ANSI port style
- ``no_ports.sv`` -- empty module edge case
- ``partial_annotations.sv`` -- mixed annotated/unannotated ports
- ``type_params.sv`` -- parametric types

Project Structure
-----------------

See :doc:`architecture` for a detailed overview of the codebase organization
and pipeline design.
