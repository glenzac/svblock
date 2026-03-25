"""Extract ModuleIR from SystemVerilog files using pyslang."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pyslang

from svblock.model import ModuleIR, ParamDef, PortDef, PortDirection


class ParseError(Exception):
    """Raised when a SystemVerilog file cannot be parsed."""


_CLOCK_PATTERN = re.compile(r"^(clk|clock)$|_clk$|_clock$", re.IGNORECASE)
_ACTIVE_LOW_PATTERN = re.compile(r"_[nNbB]$")

_DIRECTION_MAP = {
    pyslang.ArgumentDirection.In: PortDirection.INPUT,
    pyslang.ArgumentDirection.Out: PortDirection.OUTPUT,
    pyslang.ArgumentDirection.InOut: PortDirection.INOUT,
    pyslang.ArgumentDirection.Ref: PortDirection.REF,
}


def _extract_syntax_text(syntax_node: object) -> str:
    """Extract concatenated text tokens from a pyslang syntax node JSON."""
    j = json.loads(syntax_node.to_json())  # type: ignore[union-attr]
    return _collect_text(j)


def _collect_text(node: object) -> str:
    if isinstance(node, dict):
        text = node.get("text", "")
        kind = node.get("kind", "")
        if kind in ("EndOfLine", "Whitespace", "LineComment", "BlockComment"):
            return ""
        if text and kind:
            return str(text)
        return "".join(_collect_text(v) for v in node.values())
    if isinstance(node, list):
        return "".join(_collect_text(v) for v in node)
    return ""


def _get_declared_range_text(
    port: pyslang.PortSymbol,
) -> tuple[str, str] | None:
    """Get the declared range as text strings from the syntax tree.

    Returns ('WIDTH-1', '0') for parametric ranges, ('7', '0') for literals.
    Returns None for scalar (non-array) ports.
    """
    port_type = port.type
    if not port_type.isPackedArray:
        return None

    # Try to get the original text from syntax for parametric ranges
    syntax = port.syntax
    if syntax is None:
        # Fall back to elaborated values
        r = port_type.range
        return (str(r.left), str(r.right))

    parent = syntax.parent
    if parent is None:
        r = port_type.range
        return (str(r.left), str(r.right))

    try:
        header = parent.header
        data_type = header.dataType
        dims = data_type.dimensions
        for dim in dims:
            spec = dim.specifier
            sel = spec.selector
            left_text = _extract_syntax_text(sel.left)
            right_text = _extract_syntax_text(sel.right)
            if left_text and right_text:
                return (left_text, right_text)
    except (AttributeError, TypeError):
        pass

    # Fall back to elaborated values
    r = port_type.range
    return (str(r.left), str(r.right))


def _get_multidim_range_str(port_type: object) -> str | None:
    """Return a compact string like '[3:0][7:0]' for multi-dim arrays."""
    parts: list[str] = []
    t = port_type
    while hasattr(t, "isPackedArray") and t.isPackedArray:
        r = t.range
        parts.append(f"[{r.left}:{r.right}]")
        t = t.elementType
    if len(parts) > 1:
        return "".join(parts)
    return None


def _get_param_default_text(param: pyslang.ParameterSymbol) -> str | None:
    """Extract the default value of a parameter as text."""
    if not param.initializer:
        return None
    init = param.initializer
    # Try the value property first (works for int literals)
    if hasattr(init, "value") and init.value is not None:
        return str(init.value)
    # Fall back to syntax text
    if hasattr(init, "syntax") and init.syntax is not None:
        text = _extract_syntax_text(init.syntax)
        if text:
            return text
    return None


def _extract_port(port: pyslang.PortSymbol) -> PortDef:
    """Convert a pyslang PortSymbol to a PortDef."""
    port_type = port.type
    type_str = str(port_type)

    is_bus = port_type.isPackedArray
    bus_range = _get_declared_range_text(port) if is_bus else None

    # Check for multi-dimensional arrays
    multidim = _get_multidim_range_str(port_type)
    if multidim:
        type_str = f"logic {multidim}"

    return PortDef(
        name=port.name,
        direction=_DIRECTION_MAP[port.direction],
        port_type=type_str,
        is_bus=is_bus,
        bus_range=bus_range,
        is_interface=False,
        modport=None,
        has_clock_marker=bool(_CLOCK_PATTERN.search(port.name)),
        has_active_low_marker=bool(_ACTIVE_LOW_PATTERN.search(port.name)),
    )


def _extract_interface_port(port: pyslang.InterfacePortSymbol) -> PortDef:
    """Convert a pyslang InterfacePortSymbol to a PortDef."""
    iface_name = port.interfaceDef.name if port.interfaceDef else "unknown"
    modport_name = port.modport if port.modport else None

    return PortDef(
        name=port.name,
        direction=PortDirection.INTERFACE,
        port_type=iface_name,
        is_bus=False,
        bus_range=None,
        is_interface=True,
        modport=modport_name,
        has_clock_marker=False,
        has_active_low_marker=False,
    )


def _extract_param(param: object) -> ParamDef:
    """Convert a pyslang ParameterSymbol or TypeParameterSymbol to a ParamDef."""
    if isinstance(param, pyslang.TypeParameterSymbol):
        return ParamDef(
            name=param.name,
            param_type="type",
            default_value=None,
            is_localparam=param.isLocalParam,
        )

    # Regular ParameterSymbol
    type_str = str(param.type)
    default_value = _get_param_default_text(param)

    return ParamDef(
        name=param.name,
        param_type=type_str,
        default_value=default_value,
        is_localparam=param.isLocalParam,
    )


def _get_port_lines(
    body: object, source_manager: object,
) -> dict[str, int]:
    """Get a mapping of port name to source line number."""
    port_lines: dict[str, int] = {}
    for port in body.portList:  # type: ignore[attr-defined]
        loc = port.location
        line = source_manager.getLineNumber(loc)  # type: ignore[attr-defined]
        port_lines[port.name] = line
    return port_lines


def _apply_annotations(
    ports: list[PortDef],
    annotations: dict[str, dict[str, str]],
) -> list[PortDef]:
    """Apply parsed annotations to port definitions.

    Returns a new list with hidden ports removed and fields updated.
    """
    result: list[PortDef] = []
    for port in ports:
        ann = annotations.get(port.name, {})

        if ann.get("hide", "").lower() in ("true", "1", "yes"):
            continue

        # Create updated port with annotation fields
        updated = PortDef(
            name=port.name,
            direction=port.direction,
            port_type=port.port_type,
            is_bus=port.is_bus or ann.get("bus", "").lower()
            in ("true", "1", "yes"),
            bus_range=port.bus_range,
            is_interface=port.is_interface,
            modport=port.modport,
            group=ann.get("group", port.group),
            has_clock_marker=port.has_clock_marker,
            has_active_low_marker=port.has_active_low_marker,
        )
        result.append(updated)

    return result


def _extract_module_from_instance(
    inst: pyslang.InstanceSymbol,
    file_path: str,
    source_manager: object,
    source_text: str | None = None,
) -> ModuleIR:
    """Extract a ModuleIR from a pyslang InstanceSymbol."""
    body = inst.body

    ports: list[PortDef] = []
    for port in body.portList:
        if isinstance(port, pyslang.InterfacePortSymbol):
            ports.append(_extract_interface_port(port))
        elif isinstance(port, pyslang.PortSymbol):
            ports.append(_extract_port(port))

    # Apply comment annotations if source text is available
    if source_text is not None:
        from svblock.parser.annotation import parse_annotations_from_text

        port_lines = _get_port_lines(body, source_manager)
        annotations = parse_annotations_from_text(source_text, port_lines)
        ports = _apply_annotations(ports, annotations)

    params: list[ParamDef] = []
    for param in body.parameters:
        if isinstance(
            param,
            (pyslang.ParameterSymbol, pyslang.TypeParameterSymbol),
        ):
            params.append(_extract_param(param))

    return ModuleIR(
        name=inst.name,
        file_path=file_path,
        ports=ports,
        params=params,
    )


def extract_modules(
    file_path: str | Path,
    include_paths: list[str] | None = None,
) -> list[ModuleIR]:
    """Parse a SystemVerilog file and return a ModuleIR for each module found.

    Args:
        file_path: Path to the .sv or .v file.
        include_paths: Optional directories to search for `include files.

    Returns:
        List of ModuleIR, one per module definition in the file.

    Raises:
        ParseError: If the file cannot be read or parsed.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise ParseError(f"File not found: {file_path}")

    try:
        source_text = file_path.read_text(encoding="utf-8")
    except OSError as e:
        raise ParseError(f"Cannot read {file_path}: {e}") from e

    try:
        tree = pyslang.SyntaxTree.fromFile(str(file_path))
    except Exception as e:
        raise ParseError(f"Failed to parse {file_path}: {e}") from e

    comp = pyslang.Compilation()

    if include_paths:
        sm = comp.sourceManager
        if hasattr(sm, "addUserDirectories"):
            sm.addUserDirectories(include_paths)

    comp.addSyntaxTree(tree)

    diags = comp.getAllDiagnostics()
    if diags:
        for d in diags:
            severity = str(d.severity) if hasattr(d, "severity") else ""
            if "error" in severity.lower():
                raise ParseError(f"Parse error in {file_path}: {d}")

    file_str = str(file_path)
    sm = comp.sourceManager
    modules: list[ModuleIR] = []
    for inst in comp.getRoot().topInstances:
        if inst.isModule:
            modules.append(
                _extract_module_from_instance(
                    inst, file_str, sm, source_text
                )
            )

    return modules


def extract_module(
    file_path: str | Path,
    module_name: str,
    include_paths: list[str] | None = None,
) -> ModuleIR:
    """Extract a specific module by name from a SystemVerilog file.

    Raises:
        ParseError: If the file cannot be parsed or the module is not found.
    """
    modules = extract_modules(file_path, include_paths)
    for module in modules:
        if module.name == module_name:
            return module
    available = [m.name for m in modules]
    raise ParseError(
        f"Module '{module_name}' not found in {file_path}. "
        f"Available modules: {available}"
    )
