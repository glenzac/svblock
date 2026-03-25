"""Parse // @sym comment annotations from SystemVerilog source files."""

from __future__ import annotations

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

_ANNOTATION_RE = re.compile(r"//\s*@sym\s+(.+)")
_KV_RE = re.compile(r"""(\w+)\s*=\s*(?:"([^"]*)"|([\w.]+))""")


def _parse_kv_pairs(text: str) -> dict[str, str]:
    """Parse key=value or key="value" pairs from annotation text."""
    pairs: dict[str, str] = {}
    for match in _KV_RE.finditer(text):
        key = match.group(1)
        value = match.group(2) if match.group(2) is not None else match.group(3)
        pairs[key] = value
    return pairs


def parse_annotations_from_text(
    source_text: str,
    port_lines: dict[str, int],
) -> dict[str, dict[str, str]]:
    """Parse @sym annotations and associate them with ports by line number.

    Args:
        source_text: The raw SystemVerilog source text.
        port_lines: Mapping of port name to its source line number (1-based).

    Returns:
        Mapping of port name to its annotation key-value pairs.
    """
    lines = source_text.splitlines()

    # Find all annotation lines: (line_number, key-value pairs)
    annotations: list[tuple[int, dict[str, str]]] = []
    for i, line in enumerate(lines, start=1):
        match = _ANNOTATION_RE.search(line.strip())
        if match:
            pairs = _parse_kv_pairs(match.group(1))
            if pairs:
                annotations.append((i, pairs))
            else:
                logger.warning(
                    "Malformed @sym annotation on line %d: %s",
                    i,
                    match.group(1),
                )

    if not annotations:
        return {}

    # Sort ports by line number
    sorted_ports = sorted(port_lines.items(), key=lambda x: x[1])

    # Associate each annotation with the ports that follow it.
    # An annotation applies to all subsequent ports until the next annotation
    # or a blank line between annotation and port.
    result: dict[str, dict[str, str]] = {}

    for ann_line, ann_pairs in annotations:
        # Find the next annotation line (if any)
        next_ann_line = None
        for other_line, _ in annotations:
            if other_line > ann_line:
                if next_ann_line is None or other_line < next_ann_line:
                    next_ann_line = other_line

        for port_name, port_line in sorted_ports:
            if port_line <= ann_line:
                continue
            if next_ann_line is not None and port_line >= next_ann_line:
                continue

            # Check for blank lines between annotation and port
            # Only block group propagation on blank lines, not for
            # the first port directly after the annotation
            if port_line > ann_line + 1:
                has_blank = False
                for check_line in range(ann_line + 1, port_line):
                    if check_line <= len(lines):
                        content = lines[check_line - 1].strip()
                        if not content:
                            has_blank = True
                            break
                if has_blank:
                    continue

            if port_name not in result:
                result[port_name] = {}
            result[port_name].update(ann_pairs)

    return result


def parse_annotations_from_file(
    file_path: str | Path,
    port_lines: dict[str, int],
) -> dict[str, dict[str, str]]:
    """Parse @sym annotations from a file.

    Args:
        file_path: Path to the .sv or .v file.
        port_lines: Mapping of port name to its source line number.

    Returns:
        Mapping of port name to its annotation key-value pairs.
    """
    text = Path(file_path).read_text(encoding="utf-8")
    return parse_annotations_from_text(text, port_lines)
