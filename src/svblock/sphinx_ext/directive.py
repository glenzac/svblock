"""Sphinx directive for embedding svblock pin diagrams."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.application import Sphinx
from sphinx.util.docutils import SphinxDirective

from svblock import __version__
from svblock.config import load_theme
from svblock.layout.engine import LayoutConfig, compute_layout
from svblock.layout.grouping import apply_grouping
from svblock.parser import ParseError, extract_module, extract_modules
from svblock.renderer.svg_renderer import RenderOptions, render_svg


class SvblockDirective(SphinxDirective):
    """The ``.. svblock::`` directive.

    Usage::

        .. svblock:: path/to/module.sv
           :module: module_name
           :theme: dark
           :no-params:
           :no-groups:
           :no-decorators:
           :width: 400
    """

    required_arguments = 1  # SV file path
    optional_arguments = 0
    has_content = False
    option_spec: dict[str, Any] = {
        "module": directives.unchanged,
        "theme": directives.unchanged,
        "no-params": directives.flag,
        "no-groups": directives.flag,
        "no-decorators": directives.flag,
        "width": directives.positive_int,
    }

    def run(self) -> list[nodes.Node]:
        env = self.state.document.settings.env
        source_dir = Path(env.srcdir)

        # Resolve SV file relative to Sphinx source dir
        sv_rel = self.arguments[0]
        sv_path = (source_dir / sv_rel).resolve()

        if not sv_path.exists():
            return [self.state.document.reporter.warning(
                f"svblock: file not found: {sv_rel}",
                line=self.lineno,
            )]

        # Parse
        try:
            module_name = self.options.get("module")
            if module_name:
                module = extract_module(sv_path, module_name)
            else:
                modules = extract_modules(sv_path)
                if not modules:
                    return [self.state.document.reporter.warning(
                        f"svblock: no modules found in {sv_rel}",
                        line=self.lineno,
                    )]
                module = modules[0]
        except ParseError as e:
            return [self.state.document.reporter.warning(
                f"svblock: parse error: {e}",
                line=self.lineno,
            )]

        # Config
        no_params = "no-params" in self.options
        no_groups = "no-groups" in self.options
        no_decorators = "no-decorators" in self.options

        module = apply_grouping(module, flat=no_groups)

        layout_config = LayoutConfig(
            no_params=no_params,
            no_groups=no_groups,
            no_decorators=no_decorators,
        )
        if "width" in self.options:
            layout_config.min_box_width = float(self.options["width"])

        layout = compute_layout(module, layout_config)

        theme_name = self.options.get("theme", "default")
        theme = load_theme(theme_name)

        options = RenderOptions(
            no_decorators=no_decorators,
            no_params=no_params,
            standalone=False,
        )
        svg_output = render_svg(layout, theme, options)

        # Embed as raw HTML node
        raw_node = nodes.raw("", svg_output, format="html")
        return [raw_node]


def setup(app: Sphinx) -> dict[str, Any]:
    """Register the svblock directive with Sphinx."""
    app.add_directive("svblock", SvblockDirective)
    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
