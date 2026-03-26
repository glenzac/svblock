# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# -- Path setup --------------------------------------------------------------
sys.path.insert(0, os.path.abspath(os.path.join("..", "src")))

# -- Project information -----------------------------------------------------
project = "svblock"
copyright = "2026, Glen Zachariah"
author = "Glen Zachariah"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_css_files = ["css/custom.css"]

html_theme_options = {
    "logo_only": False,
    "version_selector": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": True,
    "navigation_depth": 3,
    "collapse_navigation": False,
    "sticky_navigation": True,
}

html_title = "svblock documentation"
html_short_title = "svblock"

# -- Intersphinx configuration -----------------------------------------------
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- autodoc configuration ---------------------------------------------------
autodoc_member_order = "bysource"
autodoc_typehints = "description"
