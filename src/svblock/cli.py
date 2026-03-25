"""Command-line interface for svblock."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from svblock import __version__
from svblock.config import load_theme
from svblock.layout.engine import LayoutConfig, compute_layout
from svblock.layout.grouping import apply_grouping
from svblock.parser import ParseError, extract_module, extract_modules
from svblock.renderer.svg_renderer import RenderOptions, render_svg


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="svblock",
        description="Generate pin diagrams from SystemVerilog modules.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "input_files",
        nargs="*",
        metavar="INPUT_FILE",
        help="SystemVerilog/Verilog source file(s)",
    )
    parser.add_argument(
        "-o", "--output",
        metavar="PATH",
        help="Output file path (default: <module>.<format>)",
    )
    parser.add_argument(
        "-f", "--format",
        choices=["svg", "png", "pdf"],
        default="svg",
        help="Output format (default: svg)",
    )
    parser.add_argument(
        "-m", "--module",
        metavar="TEXT",
        help="Module name to extract (default: first module found)",
    )
    parser.add_argument(
        "--theme",
        default="default",
        help="Visual theme: default, dark, minimal, print, or path to YAML/TOML file",
    )
    parser.add_argument(
        "--no-params",
        action="store_true",
        help="Suppress parameter section",
    )
    parser.add_argument(
        "--no-groups",
        action="store_true",
        help="Suppress group separators (flat port list)",
    )
    parser.add_argument(
        "--no-decorators",
        action="store_true",
        help="Suppress clock/active-low/bus decorators",
    )
    parser.add_argument(
        "--width",
        type=int,
        metavar="INTEGER",
        help="Override minimum box width in pixels",
    )
    parser.add_argument(
        "--list-modules",
        action="store_true",
        help="List all modules found in the file and exit",
    )
    parser.add_argument(
        "--sphinx",
        action="store_true",
        help="Output Sphinx-compatible SVG (standalone=false)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show parse diagnostics",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

    if not args.input_files:
        parser.print_help(sys.stderr)
        return 1

    for input_file in args.input_files:
        result = _process_file(input_file, args)
        if result != 0:
            return result
    return 0


def _process_file(input_file: str, args: argparse.Namespace) -> int:
    """Process a single input file through the full pipeline."""
    path = Path(input_file)
    if not path.exists():
        print(f"File not found: {input_file}", file=sys.stderr)
        return 1

    # Parse
    try:
        modules = extract_modules(path)
    except ParseError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        return 2

    # --list-modules mode
    if args.list_modules:
        for m in modules:
            print(m.name)
        return 0

    if not modules:
        print(f"No modules found in {input_file}", file=sys.stderr)
        return 2

    # Select module
    if args.module:
        try:
            module = extract_module(path, args.module)
        except ParseError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    else:
        module = modules[0]

    # Grouping
    module = apply_grouping(module, flat=args.no_groups)

    # Layout
    layout_config = LayoutConfig(
        no_params=args.no_params,
        no_groups=args.no_groups,
        no_decorators=args.no_decorators,
    )
    if args.width:
        layout_config.min_box_width = float(args.width)

    layout = compute_layout(module, layout_config)

    # Theme
    theme = load_theme(args.theme)

    # Render
    options = RenderOptions(
        no_decorators=args.no_decorators,
        no_params=args.no_params,
        standalone=not args.sphinx,
    )
    svg_output = render_svg(layout, theme, options)

    # Output
    fmt = args.format
    if fmt != "svg":
        print(
            f"Export format '{fmt}' not yet supported. "
            f"Install with: pip install svblock[{fmt}]",
            file=sys.stderr,
        )
        return 1

    output_path = args.output or f"{module.name}.svg"
    Path(output_path).write_text(svg_output, encoding="utf-8")

    if args.verbose:
        print(f"Wrote {output_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
