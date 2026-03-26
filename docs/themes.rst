Themes
======

svblock uses CSS custom properties (variables) for all visual styling of the
generated SVG diagrams. Four built-in themes are provided, and custom themes can
be defined in TOML or YAML files.

Built-in Themes
---------------

Select a theme with the ``--theme`` CLI option:

.. code-block:: bash

   svblock module.sv --theme dark

**default**
    Light background with colored pins. Blue inputs, red outputs. Good for
    general use and embedding in documentation.

    .. image:: _static/examples/theme_default.svg

**dark**
    Dark background inspired by Catppuccin. Pastel-colored pins on a dark
    surface. Suitable for dark-mode documentation or presentations.

    .. image:: _static/examples/theme_dark.svg

**minimal**
    Monochrome -- all pins use the same gray color. Clean look for formal
    documentation where color coding is not needed.

    .. image:: _static/examples/theme_minimal.svg

**print**
    Pure black-and-white. Designed for printing and high-contrast display.

    .. image:: _static/examples/theme_print.svg

CSS Variables
-------------

Every theme defines the following 12 CSS custom properties:

.. list-table::
   :header-rows: 1
   :widths: 30 45 25

   * - Variable
     - Purpose
     - Default Value
   * - ``--sym-bg``
     - Diagram background color
     - ``#ffffff``
   * - ``--sym-border``
     - Box border color
     - ``#333333``
   * - ``--sym-text``
     - Module name text color
     - ``#111111``
   * - ``--sym-pin-input``
     - Input pin & label color
     - ``#1a6db5``
   * - ``--sym-pin-output``
     - Output pin & label color
     - ``#b52a1a``
   * - ``--sym-pin-inout``
     - Inout pin & label color
     - ``#6a2ab5``
   * - ``--sym-pin-iface``
     - Interface pin & label color
     - ``#1a9e55``
   * - ``--sym-group-bg``
     - Group separator background
     - ``#f0f0f0``
   * - ``--sym-group-text``
     - Group label text color
     - ``#555555``
   * - ``--sym-bus-stroke``
     - Bus pin stroke width (unitless)
     - ``3``
   * - ``--sym-header-bg``
     - Header/title bar background
     - ``#e8e8e8``
   * - ``--sym-param-text``
     - Parameter text color
     - ``#666666``

Custom Themes
-------------

Create a TOML or YAML file that overrides any subset of the CSS variables. Values
you don't specify are inherited from the ``default`` theme.

TOML Format
~~~~~~~~~~~~

.. code-block:: toml

   # my_theme.toml
   [theme]
   "--sym-bg" = "#f5f5dc"
   "--sym-border" = "#8b4513"
   "--sym-pin-input" = "#006400"
   "--sym-pin-output" = "#8b0000"
   "--sym-header-bg" = "#deb887"

YAML Format
~~~~~~~~~~~~

.. code-block:: yaml

   # my_theme.yaml
   theme:
     "--sym-bg": "#f5f5dc"
     "--sym-border": "#8b4513"
     "--sym-pin-input": "#006400"
     "--sym-pin-output": "#8b0000"
     "--sym-header-bg": "#deb887"

Use the custom theme:

.. code-block:: bash

   svblock module.sv --theme my_theme.toml

.. note::

   Both flat and nested formats are supported. The ``[theme]`` / ``theme:``
   key is optional -- you can also put the variables at the top level.

   YAML support requires ``pyyaml``. TOML is supported natively on Python 3.11+;
   on Python 3.10, install ``tomli``.

Theme in Sphinx
~~~~~~~~~~~~~~~

The Sphinx directive also accepts themes:

.. code-block:: rst

   .. svblock:: path/to/module.sv
      :theme: dark
