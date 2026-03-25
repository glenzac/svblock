"""Command-line interface for svblock."""

from __future__ import annotations

import argparse
import sys

from svblock import __version__


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

    if not args.input_files:
        parser.print_help(sys.stderr)
        return 1

    # Pipeline will be wired up in Phase 9
    print(f"svblock v{__version__}: not yet implemented", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
